import asyncio
import os
from jaf import (
    run, make_litellm_provider,
    RunState, RunConfig, Message,
    generate_run_id, generate_trace_id, ModelConfig
)
from ContextClass import LearningContext
from AgentFactory import create_learning_agent

context = LearningContext(
            session_id=generate_run_id(),
            user_id="user_123",  # In real scenarios, fetch from auth system
            progress={},
            past_messages=[],
        )


# ---------------- Interactive Runner ----------------
async def interactive_learning_agent():
    """Interactive REPL for memory agent."""
    litellm_url = os.getenv("LITELLM_URL", "http://localhost:4000/")
    litellm_api_key = os.getenv("LITELLM_API_KEY", "anything")
    model_provider = make_litellm_provider(litellm_url, litellm_api_key)

    learning_agent = create_learning_agent()

    config = RunConfig(
        agent_registry={"LearningAgent": learning_agent},
        model_provider=model_provider,
        max_turns=30,
    )

    print("📝 Hi this is your personal Learning Agent - Type 'quit' to exit\n")

    i = 0



    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        if not user_input:
            continue

        state = RunState(
            run_id=generate_run_id(),
            trace_id=generate_trace_id(),
            messages=[Message(role="user", content=user_input)],
            current_agent_name="LearningAgent",
            context=context,
            turn_count=i,
        )

        result = await run(state, config)
        i += 1    

        if result.outcome.status == "completed":
            context.past_messages.append(Message(role="user", content=user_input))
            context.past_messages.append(Message(role="agent", content=result.outcome.output))
            print(f"Agent: {result.outcome.output}\n")
        else:
            print(f"Error: {result.outcome.error}\n")

# ---------------- Main ----------------
if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Loaded environment variables from .env file")
    except ImportError:
        print("⚠️ python-dotenv not installed, using system env variables")

    asyncio.run(interactive_learning_agent())