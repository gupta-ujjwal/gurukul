from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
from ..db.database import get_db
from ..models.models import Student, Progress, Course, Section
from sqlalchemy.orm import Session
import logging
from enum import Enum


class AgentType(str, Enum):
    TUTOR = "tutor"
    BUDDY = "buddy"

# ---------------- LangGraph State ----------------
class LearningState(TypedDict):
    """LangGraph state for the learning agent."""
    messages: Annotated[List[BaseMessage], operator.add]
    learning_context: "LearningContext"

# ---------------- Legacy Context (for compatibility) ----------------
@dataclass
class LearningContext:
    """Learning context for the agent."""
    user_id: str
    session_id: str
    created_at: Optional[datetime] = None
    progress: Optional[Dict[str, Any]] = None
    past_messages: Optional[List[Dict[str, str]]] = None
    current_agent: AgentType = AgentType.BUDDY

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.progress is None:
            self.progress = {}
        if self.past_messages is None:
            self.past_messages = []
        # Default to buddy agent for new sessions
        if not hasattr(self, 'current_agent') or self.current_agent is None:
            self.current_agent = AgentType.BUDDY

    def add_message(self, role: str, content: str):
        """Add a message to the past messages."""
        if self.past_messages is None:
            self.past_messages = []
        self.past_messages.append({"role": role, "content": content})

    def get_messages_as_langchain(self) -> List[BaseMessage]:
        """Convert past messages to LangChain message format."""
        messages = []
        if self.past_messages:
            for msg in self.past_messages:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] in ["assistant", "agent"]:
                    messages.append(AIMessage(content=msg["content"]))
        return messages

    def update_progress(self, chapter: str, section: str, score: int):
        """Update progress for a chapter and section in the database."""
        db_generator = get_db()
        db = next(db_generator)
        try:
            # Find the student by user_id
            student = db.query(Student).filter(Student.username == self.user_id).first()
            if not student:
                raise ValueError(f"Student with username {self.user_id} not found. Please ensure the user is properly registered.")
            
            # For now, just update in-memory progress since the Progress model
            # requires valid course_id, chapter_id, section_id which we don't have
            if self.progress is None:
                self.progress = {}
            self.progress[(chapter, section)] = score
            
            logging.info(f"Progress updated in memory for {self.user_id}: {chapter}, {section}, {score}")
            
        except Exception as e:
            db.rollback()
            logging.error(f"Error updating progress: {str(e)}")
            raise
        finally:
            # Let the generator handle closing the session
            try:
                next(db_generator)
            except StopIteration:
                pass

    def get_progress_summary(self) -> str:
        """Get a formatted progress summary from memory (simplified for now)."""
        try:
            if not self.progress:
                return "No progress recorded yet."
            
            progress_lines = ["Your Progress:"]
            for (chapter, section), score in self.progress.items():
                progress_lines.append(f"- Chapter: {chapter}, Section: {section}, Score: {score}/100")
            
            return "\n".join(progress_lines)
            
        except Exception as e:
            logging.error(f"Error getting progress summary: {str(e)}")
            return "Error retrieving progress."