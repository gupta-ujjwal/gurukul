import asyncio
import os
from ContextClass import LearningContext
from AgentFactory import create_learning_agent, run_learning_agent_async

# Initialize learning context
context = LearningContext(
    session_id="cli_session_001",
    user_id="user_123",  # In real scenarios, fetch from auth system
    progress={},
    past_messages=[],
)

# ---------------- Interactive Runner ----------------
async def interactive_learning_agent():
    """Interactive REPL for LangGraph learning agent."""
    
    print("📝 Hi this is your personal Learning Agent - Type 'quit' to exit\n")
    
    # Create the LangGraph agent
    agent_graph = create_learning_agent()
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        if not user_input:
            continue

        try:
            # Run the agent with user input
            response = await run_learning_agent_async(agent_graph, user_input, context)
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