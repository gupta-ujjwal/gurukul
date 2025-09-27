import time
from langgraph.graph import END, StateGraph
from src.agents.ContextClass import LearningState
from src.tools.ToolFactory import LEARNING_TOOLS
from src.utils.agent_utils import print_log, log_step_entry, log_step_exit, should_continue, llm_call
from src.agents.prompts.buddy_prompt import BUDDY_SYSTEM_PROMPT, TRANSFER_TO_TUTOR_TEXT
from langgraph.prebuilt import ToolNode


def create_buddy_subgraph():
    """Create buddy subgraph"""
    workflow = StateGraph(LearningState)
    
    def buddy_agent(state: LearningState) -> dict:
        """Node function for buddy agent"""
        start_time = time.time()
        log_step_entry(state, "BUDDY_AGENT", {"agent_type": "BUDDY"})
        print_log(state, "Buddy agent activated")
        
        system_message = BUDDY_SYSTEM_PROMPT.format(transfer_to_tutor_text=TRANSFER_TO_TUTOR_TEXT)
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