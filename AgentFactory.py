# AgentFactory.py
from jaf import (
    Agent, ModelConfig
)
from ContextClass import LearningContext
from ToolFactory import get_course, get_section_context, view_progress, update_progress


# ---------------- Agent ----------------
def create_learning_agent() -> Agent:
    """Create the local learning agent."""

    def instructions(state):
        
        session_context = state.context.session_metadata if state.context and state.context.session_metadata else {}
        
        return f"""
        You are a CBSE Class 11 Physics tutor. STRICT RULES:
            1) Use ONLY the local NCERT content provided via tools; never use outside knowledge.
            3) If the tools return no snippets or an error, politely refuse and ask the user to pick a valid chapter/section.
            Capabilities you should use in chat:
            - Call get_course to show the course map (chapters and sections). Format it nicely and present to the user.
            - When the user selects a section, call get_section_context to fetch section data. Summarize it and teach it to the user
              using a 5-part flow (recall, teach with visuals-in-words, guided practice, quick check, reflect), Add ELI10 examples.
            - For a quick test, generate 3-5 MCQs with 4 options each, and provide answers if the user asks for it.
            - After test submission by student, call update_progress with a score out of 100 based on the user's responses.
            - At any time, the user can call view_progress to see their progress.

        Always be friendly, patient, and encouraging. Your goal is to help the user learn effectively using only the provided materials. 
        Also remember the attached session context to give relevant answers : {session_context}
        """

    return Agent(
        name="LearningAgent",
        instructions=instructions,
        model_config=ModelConfig(
            name="qwen3-coder-480b"  # Or whichever model litellm is serving
        ),
        tools=[get_course, get_section_context, view_progress, update_progress],
    )
