import time
from langgraph.graph import END, StateGraph
from src.agents.ContextClass import LearningState
from src.tools.ToolFactory import LEARNING_TOOLS
from src.utils.agent_utils import print_log, log_step_entry, log_step_exit, should_continue, llm_call
from src.agents.prompts.tutor_prompt import TUTOR_SYSTEM_PROMPT, TRANSFER_TO_BUDDY_TEXT
from langgraph.prebuilt import ToolNode


def create_tutor_subgraph():
    """Create tutor subgraph"""
    workflow = StateGraph(LearningState)
    
    def tutor_agent(state: LearningState) -> dict:
        """Node function for tutor agent"""
        start_time = time.time()
        log_step_entry(state, "TUTOR_AGENT", {"agent_type": "TUTOR"})
        print_log(state, "Tutor agent activated")
        
        system_message = TUTOR_SYSTEM_PROMPT.format(transfer_to_buddy_text=TRANSFER_TO_BUDDY_TEXT)
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