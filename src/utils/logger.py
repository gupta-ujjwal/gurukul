import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False

class LearningAgentLogger:
    """Centralized logger for the Learning Agent with structured logging capabilities."""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize the logger with file and console handlers."""
        self.log_dir = log_dir
        
        # Ensure logs directory exists in project root
        if not os.path.isabs(self.log_dir):
            # Make log_dir relative to project root (not src/)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.log_dir = os.path.join(project_root, self.log_dir)
            
        self.ensure_log_directory()
        
        # Create main logger
        self.logger = logging.getLogger("learning_agent")
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Setup file handler for structured logs
        self.setup_file_handler()
        
        # Setup console handler for colored output
        self.setup_console_handler()
    
    def ensure_log_directory(self):
        """Ensure the log directory exists."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def setup_file_handler(self):
        """Setup rotating file handler for JSON structured logs with timestamp-based filename."""
        # Generate timestamp-based filename for this server run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"learning_agent_{timestamp}.log")
        
        # Store the current log file path for reference
        self.current_log_file = log_file
        
        # Rotating file handler (10MB max, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # JSON formatter for structured logging
        file_formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(file_handler)
    
    def setup_console_handler(self):
        """Setup colored console handler for readable output."""
        if HAS_COLORLOG:
            console_handler = colorlog.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Colored formatter for console
            console_formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(levelname)s - %(message)s%(reset)s',
                datefmt='%H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(console_formatter)
        else:
            # Fallback to regular console handler without colors
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Regular formatter for console
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
    
    def log_step(
        self, 
        step_name: str, 
        status: str, 
        user_id: Optional[str] = None, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        level: str = "INFO"
    ):
        """Log a workflow step with structured data."""
        
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "step": step_name,
            "status": status,
            "level": level
        }
        
        # Add optional fields
        if user_id:
            log_entry["user_id"] = user_id
        if session_id:
            log_entry["session_id"] = session_id
        if context:
            log_entry["context"] = context
        
        # Log as JSON for file handler
        json_message = json.dumps(log_entry)
        
        # Log as readable text for console
        readable_parts = [f"[{step_name}] {status}"]
        if user_id:
            readable_parts.append(f"User: {user_id}")
        if session_id:
            readable_parts.append(f"Session: {session_id}")
        if context:
            readable_parts.append(f"Context: {context}")
        
        readable_message = " | ".join(readable_parts)
        
        # Log to both handlers
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # File handler gets JSON
        for handler in self.logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                handler.emit(logging.LogRecord(
                    name=self.logger.name,
                    level=log_level,
                    pathname="",
                    lineno=0,
                    msg=json_message,
                    args=(),
                    exc_info=None
                ))
            else:
                # Console handler gets readable format
                handler.emit(logging.LogRecord(
                    name=self.logger.name,
                    level=log_level,
                    pathname="",
                    lineno=0,
                    msg=readable_message,
                    args=(),
                    exc_info=None
                ))
    
    def log_entry(
        self, 
        step_name: str, 
        user_id: Optional[str] = None, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log step entry."""
        self.log_step(step_name, "ENTER", user_id, session_id, context, "INFO")
    
    def log_exit(
        self, 
        step_name: str, 
        user_id: Optional[str] = None, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ):
        """Log step exit with optional duration."""
        exit_context = context or {}
        if duration_ms is not None:
            exit_context["duration_ms"] = duration_ms
        
        self.log_step(step_name, "EXIT", user_id, session_id, exit_context, "INFO")
    
    def log_error(
        self, 
        step_name: str, 
        error_message: str,
        user_id: Optional[str] = None, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log step error."""
        error_context = context or {}
        error_context["error"] = error_message
        
        self.log_step(step_name, "ERROR", user_id, session_id, error_context, "ERROR")
    
    def log_transition(
        self,
        from_step: str,
        to_step: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log workflow transitions."""
        transition_context = context or {}
        transition_context["from_step"] = from_step
        transition_context["to_step"] = to_step
        
        self.log_step("TRANSITION", "EXECUTE", user_id, session_id, transition_context, "DEBUG")


# Global logger instance
_logger_instance = None

def get_logger() -> LearningAgentLogger:
    """Get the global logger instance (singleton pattern)."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = LearningAgentLogger()
    return _logger_instance