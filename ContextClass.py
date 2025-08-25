
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any
from jaf import Message
# ---------------- Context ----------------
@dataclass(frozen=True)
class LearningContext:
    """Immutable context for learning agent."""
    user_id: str
    session_id: str
    created_at: datetime = None
    progress: Optional[Dict[str, Any]] = None
    past_messages: Optional[Message] = None

    def __post_init__(self):
        if self.created_at is None:
            object.__setattr__(self, 'created_at', datetime.utcnow())
