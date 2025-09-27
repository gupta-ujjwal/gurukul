# AgentFactory.py
import os
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_litellm import ChatLiteLLM
from .ContextClass import LearningContext, LearningState, AgentType
from ..tools.ToolFactory import LEARNING_TOOLS, set_current_context
from .Agents import create_agent_graph

# ---------------- LangGraph Agent ----------------

def create_learning_agent() -> StateGraph:
    """Create the LangGraph-based learning agent with buddy and tutor subgraphs."""
    return create_agent_graph()

# ---------------- Utility Functions ----------------

def run_learning_agent(agent_graph: StateGraph, user_input: str, context: LearningContext) -> str:
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

async def run_learning_agent_async(agent_graph: StateGraph, user_input: str, context: LearningContext) -> str:
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