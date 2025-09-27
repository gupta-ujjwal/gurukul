import os
import time
from langgraph.graph import END, StateGraph
from src.agents.ContextClass import AgentType, LearningState
from src.tools.ToolFactory import LEARNING_TOOLS
from langchain_litellm import ChatLiteLLM
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.prebuilt import ToolNode
from src.utils.logger import get_logger


transfer_to_buddy_text = "Transferring you to Buddy now."
transfer_to_tutor_text = "Transferring you to Tutor now."

def print_log(state: LearningState, message: str, step_name: str = None, status: str = "INFO", context: dict = None):
    """Enhanced utility function to print logs with structured logging."""
    logger = get_logger()
    
    user_id = state["learning_context"].user_id if state.get("learning_context") else "unknown"
    session_id = state["learning_context"].session_id if state.get("learning_context") else "unknown"
    
    # If step_name provided, use structured logging
    if step_name:
        logger.log_step(
            step_name=step_name,
            status=status,
            user_id=user_id,
            session_id=session_id,
            context=context
        )
    else:
        # Fallback to basic logging for backward compatibility
        logger.log_step(
            step_name="GENERAL",
            status="INFO",
            user_id=user_id,
            session_id=session_id,
            context={"message": message}
        )
    
    # Keep console output for immediate visibility (optional)
    print(f"{'='*60}\n")
    print(f"[User: {user_id} | Session: {session_id}] {message}")
    print(f"{'='*60}\n")

def log_step_entry(state: LearningState, step_name: str, context: dict = None):
    """Log entry into a workflow step."""
    logger = get_logger()
    user_id = state["learning_context"].user_id if state.get("learning_context") else "unknown"
    session_id = state["learning_context"].session_id if state.get("learning_context") else "unknown"
    
    logger.log_entry(step_name, user_id, session_id, context)
    
def log_step_exit(state: LearningState, step_name: str, context: dict = None, start_time: float = None):
    """Log exit from a workflow step with optional timing."""
    logger = get_logger()
    user_id = state["learning_context"].user_id if state.get("learning_context") else "unknown"
    session_id = state["learning_context"].session_id if state.get("learning_context") else "unknown"
    
    duration_ms = None
    if start_time:
        duration_ms = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    logger.log_exit(step_name, user_id, session_id, context, duration_ms)

def should_continue(state: LearningState):
    """Determine if we should continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the last message has tool calls, continue to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print_log(state, f"Agent has tool calls: {[call.get('name', 'unknown') for call in last_message.tool_calls]}")
        return "tools"
    # Otherwise, we're done
    print_log(state, "Agent completed without tool calls")
    return END

def llm_call(system_message: str, state: LearningState) -> AIMessage:
    """Call LLM via LiteLLM using environment configuration with enhanced analytics tracking."""
    start_time = time.time()
    
    try:
        log_step_entry(state, "LLM_CALL", {"model": os.getenv('MODEL_NAME', 'claude-4')})
        print_log(state, f"Calling LLM with model: {os.getenv('MODEL_NAME', 'claude-4')}")
        
        # Initialize the LLM
        litellm_url = os.getenv("LITELLM_URL", "http://localhost:4000/")
        litellm_api_key = os.getenv("LITELLM_API_KEY", "anything")
        litellm_model = os.getenv("MODEL_NAME", "claude-4")

         # Initialize LLM via LiteLLM
        llm = ChatLiteLLM(
            model=litellm_model,   # LiteLLM model name
            api_key=litellm_api_key, # or rely on env var
            api_base=litellm_url
        )

        # TODO - Attach the right tools based on current agent
        llm_with_tools = llm.bind_tools(LEARNING_TOOLS)

        system_message = SystemMessage(content=system_message)

        messages = [system_message] + state["messages"]
        print_log(state, f"Sending {len(messages)} messages to LLM")
        response = llm_with_tools.invoke(messages)
        
        print_log(state, f"LLM response received: {len(response.content)} characters")
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print_log(state, f"LLM requested {len(response.tool_calls)} tool calls")

        log_step_exit(state, "LLM_CALL", {
            "response_length": len(response.content),
            "tool_calls_count": len(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else 0
        }, start_time)

        # Return the original response to preserve tool calls
        return response

    except Exception as e:
        print_log(state, f"LLM call failed: {str(e)}")
        log_step_exit(state, "LLM_CALL", {"error": str(e)}, start_time)
        return AIMessage(content=f"LLM Error: {str(e)}")

def create_buddy_subgraph():
    """Create buddy subgraph"""
    workflow = StateGraph(LearningState)
    
    def buddy_agent(state: LearningState) -> dict:
        """Node function for buddy agent"""
        start_time = time.time()
        log_step_entry(state, "BUDDY_AGENT", {"agent_type": "BUDDY"})
        print_log(state, "Buddy agent activated")
        
        system_message = f"""
        You are a friendly and supportive study buddy for a class 11 CBSE student. Be friendly, patient, and encouraging at all times. 
        
        Your primary responsibilities are:
        - Assist the student with course structure, progress tracking, and answering questions based on their existing knowledge and the provided materials.
        - Help the student reflect on what they have learned and motivate them to continue their studies.

        Guidelines:
        - If the student asks about new concepts or topics they have not yet learned, do NOT attempt to teach. Instead, reply with exactly this text: {transfer_to_tutor_text}.
        - If the student asks questions beyond their current knowledge or outside the provided materials, reply with exactly this text: {transfer_to_tutor_text}.
        - For all other queries, provide clear, concise, and helpful answers using only the provided materials and the student's current knowledge.
        - Never use information or resources outside the provided materials.
        - Always encourage the student and acknowledge their efforts.

        Formatting:
        - ALL RESPONSES MUST BE IN PROPER HTML FORMAT WITH APPROPRIATE TAGS (such as <b>, <ul>, <li>, <h2>, etc.). NEVER USE MARKDOWN OR PLAIN TEXT.
        - Use bullet points, headings, and bold text to highlight key information and make your responses easy to read.

        Remember: If you are unsure or the question is outside your scope, transfer the student to the tutor agent with exactly this text: {transfer_to_tutor_text}
        """
        response = llm_call(system_message, state)
        print_log(state, "Buddy agent response generated")
        
        log_step_exit(state, "BUDDY_AGENT", {
            "response_length": len(response.content),
            "has_tool_calls": hasattr(response, 'tool_calls') and bool(response.tool_calls)
        }, start_time)
        
        return {"messages": [response]}
    
    workflow.add_node("buddy_agent", buddy_agent)
    workflow.add_node("tools", ToolNode(LEARNING_TOOLS))
    workflow.set_entry_point("buddy_agent")
    
    workflow.add_conditional_edges(
        "buddy_agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        }
    )
    
    workflow.add_edge("tools", "buddy_agent")
    
    return workflow.compile()

def create_tutor_subgraph():
    """Create tutor subgraph"""
    workflow = StateGraph(LearningState)
    
    def tutor_agent(state: LearningState) -> dict:
        """Node function for tutor agent"""
        start_time = time.time()
        log_step_entry(state, "TUTOR_AGENT", {"agent_type": "TUTOR"})
        print_log(state, "Tutor agent activated")
        
        system_message = f"""
        You are a knowledgeable and patient tutor for a class 11 CBSE student. 
        Your primary responsibility is to teach new concepts, provide detailed explanations, 
        and guide the student through exercises using only the provided NCERT materials and tools. 
        Do not use any outside knowledge or resources.

        Your teaching process must follow this 5-part flow for every new concept:
        1. <b>Recall</b>: Briefly review what the student already knows about the topic.
        2. <b>Teach with Visuals-in-Words</b>: Explain the concept clearly, using vivid descriptions as if painting a picture with words. Use ELI10 (Explain Like I'm 10) examples wherever possible.
        3. <b>Guided Practice</b>: Walk the student through an example or exercise step-by-step.
        4. <b>Quick Check</b>: Ask a short question to check the student's understanding.
        5. <b>Reflect</b>: Summarize the key points and encourage the student to reflect on what they've learned.

        After teaching a section, always ask the student if they have any questions. 
        If they do, answer them using only the content from the current section. 
        If they don't have questions, offer to conduct a quick test using 3-5 multiple-choice questions (MCQs) with 4 options each. Provide answers only if the student asks for them.

        After the student submits their answers, call the <b>update_progress</b> tool with a score out of 100 based on their responses.
        
        If the student asks about course structure, progress tracking, or anything outside the scope of teaching, politely inform them that you will transfer them to the buddy agent for those queries. Respond with exactly this text: {transfer_to_buddy_text}
        If the student asks questions outside the provided materials, inform them that you can only assist with the provided content.
        All your responses must be formatted in proper HTML with appropriate tags, headings, bullet points, and bold text for key concepts. Never use markdown or plain text.
        Once you have finished teaching, transfer the student to the buddy agent for general queries and progress tracking. Respond with exactly this text: {transfer_to_buddy_text}
        """
        response = llm_call(system_message, state)
        print_log(state, "Tutor agent response generated")
        
        log_step_exit(state, "TUTOR_AGENT", {
            "response_length": len(response.content),
            "has_tool_calls": hasattr(response, 'tool_calls') and bool(response.tool_calls)
        }, start_time)
        
        return {"messages": [response]}
    
    workflow.add_node("tutor_agent", tutor_agent)
    workflow.add_node("tools", ToolNode(LEARNING_TOOLS))
    workflow.set_entry_point("tutor_agent")
    
    workflow.add_conditional_edges(
        "tutor_agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        }
    )
    
    workflow.add_edge("tools", "tutor_agent")
    
    return workflow.compile()

def update_agent_node(state: LearningState) -> dict:
    """Node to update the current agent based on context."""
    start_time = time.time()
    log_step_entry(state, "UPDATE_AGENT", {"current_agent": state["learning_context"].current_agent.value})
    print_log(state, "Update agent node activated")
    
    if transfer_to_buddy_text in state["messages"][-1].content:
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
        
    elif transfer_to_tutor_text in state["messages"][-1].content:    
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
        "transfer_occurred": transfer_to_buddy_text in state["messages"][-1].content or transfer_to_tutor_text in state["messages"][-1].content
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