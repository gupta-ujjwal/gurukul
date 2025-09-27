import time
from langgraph.graph import StateGraph, END
from src.agents.ContextClass import AgentType, LearningState
from src.utils.agent_utils import print_log, log_step_entry, log_step_exit
from src.utils.logger import get_logger
from src.agents.buddy_agent import create_buddy_subgraph
from src.agents.tutor_agent import create_tutor_subgraph
from src.agents.prompts.buddy_prompt import TRANSFER_TO_BUDDY_TEXT, TRANSFER_TO_TUTOR_TEXT
from langchain_core.messages import AIMessage, HumanMessage
from ..tools.ToolFactory import set_current_context


def update_agent_node(state: LearningState) -> dict:
    """Node to update the current agent based on context."""
    start_time = time.time()
    log_step_entry(state, "UPDATE_AGENT", {"current_agent": state["learning_context"].current_agent.value})
    print_log(state, "Update agent node activated")
    
    if TRANSFER_TO_BUDDY_TEXT in state["messages"][-1].content:
        # add an AssistantMessage to state.messages indicating transfer
        print_log(state, "Transferring to Buddy agent")
        state["messages"].append(AIMessage(content="Transferring you to Buddy now."))
        state["learning_context"].current_agent = AgentType.BUDDY
        
        logger = get_logger()
        logger.log_transition(
            from_step="TUTOR_AGENT",
            to_step="BUDDY_AGENT",
            user_id=state["learning_context"].user_id,
            session_id=state["learning_context"].session_id,
            context={"transfer_reason": "tutor_to_buddy_request"}
        )
        
    elif TRANSFER_TO_TUTOR_TEXT in state["messages"][-1].content:    
        print_log(state, "Transferring to Tutor agent")
        state["messages"].append(AIMessage(content="Transferring you to Tutor now."))
        state["learning_context"].current_agent = AgentType.TUTOR
        
        logger = get_logger()
        logger.log_transition(
            from_step="BUDDY_AGENT",
            to_step="TUTOR_AGENT",
            user_id=state["learning_context"].user_id,
            session_id=state["learning_context"].session_id,
            context={"transfer_reason": "buddy_to_tutor_request"}
        )
        
    else:
        print_log(state, "No agent transfer needed")

    log_step_exit(state, "UPDATE_AGENT", {
        "final_agent": state["learning_context"].current_agent.value,
        "transfer_occurred": TRANSFER_TO_BUDDY_TEXT in state["messages"][-1].content or TRANSFER_TO_TUTOR_TEXT in state["messages"][-1].content
    }, start_time)

    return state

def create_agent_graph(): 

    def start_node(state: LearningState) -> LearningState:
        """Initial node to start the workflow."""
        start_time = time.time()
        log_step_entry(state, "WORKFLOW_START", {
            "initial_agent": state["learning_context"].current_agent.value,
            "message_count": len(state["messages"])
        })
        print_log(state, "Starting the learning agent workflow.")
        
        log_step_exit(state, "WORKFLOW_START", {
            "status": "initialized"
        }, start_time)
        
        return state
    
    def end_node(state: LearningState) -> LearningState:
        """End node to conclude the workflow."""
        start_time = time.time()
        log_step_entry(state, "WORKFLOW_END", {
            "final_agent": state["learning_context"].current_agent.value,
            "total_messages": len(state["messages"])
        })
        print_log(state, "Ending the learning agent workflow.")
        
        log_step_exit(state, "WORKFLOW_END", {
            "status": "completed"
        }, start_time)
        
        return state
    
    workflow = StateGraph(LearningState)
    workflow.add_node("start", start_node)
    workflow.add_node("update_agent", update_agent_node)
    workflow.add_node("end", end_node)

    # Compile subgraphs first
    buddy_subgraph = create_buddy_subgraph()
    tutor_subgraph = create_tutor_subgraph()

    # Add subgraphs as nodes
    workflow.add_node("buddy_subgraph", buddy_subgraph)
    workflow.add_node("tutor_subgraph", tutor_subgraph)

    workflow.set_entry_point("start")
    
    workflow.add_conditional_edges(
        "start",
        lambda state: state["learning_context"].current_agent,
        {
            AgentType.TUTOR: "tutor_subgraph",
            AgentType.BUDDY: "buddy_subgraph",
        }
    )

    workflow.add_edge("tutor_subgraph", "update_agent")
    workflow.add_edge("buddy_subgraph", "update_agent")
    workflow.add_edge("update_agent", "end")
    
    # Set finish point
    workflow.set_finish_point("end")

    # Compile the graph
    app = workflow.compile()
    
    graph = app.get_graph()
    graph.print_ascii()
    
    return app

# ---------------- Agent Execution Functions ----------------

def create_learning_agent():
    """Create the LangGraph-based learning agent with buddy and tutor subgraphs."""
    return create_agent_graph()

def run_learning_agent(agent_graph, user_input: str, context) -> str:
    """Run the learning agent with user input and return the response."""
    
    # Set the current context for tools
    set_current_context(context)
    
    # Get conversation history
    past_messages = context.get_messages_as_langchain()
    
    # Create the initial state
    initial_state = LearningState(
        messages=past_messages + [HumanMessage(content=user_input)],
        learning_context=context
    )
    
    # Run the agent
    result = agent_graph.invoke(initial_state)
    
    # Get the final response
    final_messages = result["messages"]
    if final_messages:
        last_message = final_messages[-1]
        if isinstance(last_message, AIMessage):
            response = last_message.content
            
            # Update context with new messages
            context.add_message("user", user_input)
            context.add_message("assistant", response)
            
            return response
    
    return "I apologize, but I encountered an error processing your request."

async def run_learning_agent_async(agent_graph, user_input: str, context) -> str:
    """Async version of run_learning_agent."""
    
    # Set the current context for tools
    set_current_context(context)
    
    # Get conversation history
    past_messages = context.get_messages_as_langchain()
    
    # Create the initial state
    initial_state = LearningState(
        messages=past_messages + [HumanMessage(content=user_input)],
        learning_context=context
    )
    
    # Run the agent asynchronously
    result = await agent_graph.ainvoke(initial_state)
    
    # Get the final response
    final_messages = result["messages"]
    if final_messages:
        last_message = final_messages[-1]
        if isinstance(last_message, AIMessage):
            response = last_message.content
            
            # Update context with new messages
            context.add_message("user", user_input)
            context.add_message("assistant", response)
            
            return response
    
    return "I apologize, but I encountered an error processing your request."