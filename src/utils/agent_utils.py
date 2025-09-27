import os
import time
from src.agents.ContextClass import LearningState
from src.utils.logger import get_logger


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
    from langgraph.graph import END
    
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the last message has tool calls, continue to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print_log(state, f"Agent has tool calls: {[call.get('name', 'unknown') for call in last_message.tool_calls]}")
        return "tools"
    # Otherwise, we're done
    print_log(state, "Agent completed without tool calls")
    return END

def llm_call(system_message: str, state: LearningState):
    """Call LLM via LiteLLM using environment configuration with enhanced analytics tracking."""
    from langchain_litellm import ChatLiteLLM
    from langchain_core.messages import SystemMessage, AIMessage
    from src.tools.ToolFactory import LEARNING_TOOLS
    
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
        from langchain_core.messages import AIMessage
        return AIMessage(content=f"LLM Error: {str(e)}")