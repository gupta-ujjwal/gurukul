import asyncio
import os
from ContextClass import LearningContext
from AgentFactory import create_learning_agent, run_learning_agent_async

# Learning context will be created dynamically
context = None

# ---------------- Interactive Runner ----------------
def get_cli_context():
    """Get or create learning context for CLI usage."""
    global context
    
    if context is None:
        # For CLI usage, create a temporary context
        # In a real implementation, you might want to authenticate users
        context = LearningContext(
            user_id="cli_user",
            session_id="cli_session",
            progress={},
            past_messages=[],
        )
    
    return context

async def interactive_learning_agent():
    """Interactive REPL for LangGraph learning agent."""
    
    print("📝 Hi this is your personal Learning Agent - Type 'quit' to exit\n")
    print("Note: CLI mode uses temporary session. Data will not be persisted.\n")
    
    # Create the LangGraph agent
    agent_graph = create_learning_agent()
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        if not user_input:
            continue

        try:
            # Get context and run the agent with user input
            cli_context = get_cli_context()
            response = await run_learning_agent_async(agent_graph, user_input, cli_context)
            print(f"Agent: {response}\n")
            
        except Exception as e:
            print(f"Error: {str(e)}\n")

# ---------------- Main ----------------
if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Loaded environment variables from .env file")
    except ImportError:
        print("⚠️ python-dotenv not installed, using system env variables")

    asyncio.run(interactive_learning_agent())