
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any

# ---------------- Context ----------------
@dataclass(frozen=True)
class LearningContext:
    """Immutable context for learning agent."""
    user_id: str = None
    session_id: str = None
    created_at: datetime = None
    progress: Optional[Dict[str, Any]] = None
    session_metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            object.__setattr__(self, 'created_at', datetime.utcnow())
