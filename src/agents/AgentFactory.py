# AgentFactory.py
import os
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_litellm import ChatLiteLLM
from .ContextClass import LearningContext, LearningState
from ..tools.ToolFactory import LEARNING_TOOLS, set_current_context

# ---------------- LangGraph Agent ----------------

def create_learning_agent() -> StateGraph:
    """Create the LangGraph-based learning agent."""
    
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
    
    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(LEARNING_TOOLS)
    
    # System instructions
    system_message = SystemMessage(content="""
    You are a CBSE Class 11 Physics tutor. STRICT RULES:
        1) Use ONLY the local NCERT content provided via tools; never use outside knowledge.
        2) If the tools return no snippets or an error, politely refuse and ask the user to pick a valid chapter/section.
        3) ALL RESPONSES MUST BE IN PROPER HTML FORMAT WITH TAGS. NEVER USE MARKDOWN SYNTAX OR PLAIN TEXT.

        
        Capabilities you should use in chat:
        - Call get_course to get the course map (chapters and sections). Format it nicely and present to the user.
        - Based on user's progress so far (available via view_progress), suggest the next section to study.
        - Based on user's choice call get_section_context to fetch section data. 
          Summarize it and teach it to the user using a 5-part flow (recall, teach with visuals-in-words, guided practice, quick check, reflect), 
          Add ELI10 examples wherever applicable.
        - Format the teaching content in simple HTML with headings, bullet points, and bold text for key concepts.
        - Ask the user if they have any questions after teaching a section. If they do, answer them using only the section content
        - If they dont have any questions offer to conduct a quick test using MCQs. Generate 3-5 MCQs with 4 options each, and provide answers if the user asks for it.
        - After test submission by student, call update_progress with a score out of 100 based on the user's responses.
        - At any time, the user can call view_progress to see their progress.

    Always be friendly, patient, and encouraging. 
    Your goal is to help the user learn effectively using only the provided materials.
    Your target audience is a 15-17 year old student. Use simple language and explain concepts clearly.
    """)
    
    def call_model(state: LearningState):
        """Call the LLM with the current state."""
        messages = [system_message] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    def should_continue(state: LearningState):
        """Determine if we should continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the last message has tool calls, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        # Otherwise, we're done
        return END
    
    # Create the graph
    workflow = StateGraph(LearningState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(LEARNING_TOOLS))
    
    # Set the entrypoint
    workflow.set_entry_point("agent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        }
    )
    
    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")
    

    # Compile the graph
    app = workflow.compile()
    
    graph = app.get_graph()
    graph.print_ascii()
    
    return app

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