import os
from langchain_core.tools import tool
from ContextClass import LearningContext, LearningState
from typing import List
import re  

# Global context reference (will be set by the agent)
_current_context: LearningContext = None

def set_current_context(context: LearningContext):
    """Set the current learning context for tools to access."""
    global _current_context
    _current_context = context

def get_current_context() -> LearningContext:
    """Get the current learning context."""
    global _current_context
    if _current_context is None:
        raise ValueError("No learning context is currently set")
    return _current_context

# ---------------- LangGraph Tools ----------------

@tool
def update_progress(chapter: str, section: str, score: int) -> str:
    """Update user progress for a chapter and section with a score out of 100.
    
    Args:
        chapter: The chapter name or number
        section: The section name 
        score: Score out of 100
    """
    context = get_current_context()
    context.update_progress(chapter, section, score)
    
    return f"Progress updated: Chapter '{chapter}', Section '{section}', Score {score}/100."

@tool 
def view_progress() -> str:
    """View user progress across chapters and sections."""
    context = get_current_context()
    return context.get_progress_summary()

@tool
def get_course() -> str:
    """Fetch the course map showing available chapters and sections."""
    
    # Simulated course map
    return """
    Course: CBSE Class 11 Physics
    UNIT I: PHYSICAL WORLD AND MEASUREMENT 
        Chapter 1 – Units and Measurements 

        Need for measurement: Units of measurement; systems of units; SI units, fundamental and derived units. significant figures. Dimensions of physical quantities, dimensional analysis and its applications. 

        UNIT II: KINEMATICS 
        Chapter 2 – Motion in a Straight Line 

        Frame of reference, Motion in a straight line, Elementary concepts of differentiation and integration for describing motion, uniform and non- uniform motion, and instantaneous velocity, uniformly accelerated motion, velocity - time and position-time graphs. Relations for uniformly accelerated motion (graphical treatment).
    """

@tool
def get_section_context(chapter: str, section: str) -> str:
    """Fetch content snippets and citations for a specific chapter and section.
    
    Args:
        chapter: The chapter name or number
        section: The section name
    """
    
    # Simulated content retrieval
    if chapter == "1" or section == "Units and Measurements":
        content = extract_pages_from_pdf("/Users/Ujjwal.gupta/juspay/Playground/jaf/learning-agent/LerningMaterial/Class 11/Physics/keph101.pdf")
        if not content:
            return "No content found for Chapter 1 - Units and Measurements."
        return "\n".join(content)
    elif chapter == "2" or section == "Motion in a Straight Line":
        content = extract_pages_from_pdf("/Users/Ujjwal.gupta/juspay/Playground/jaf/learning-agent/LerningMaterial/Class 11/Physics/keph102.pdf")
        if not content:
            return "No content found for Chapter 2 - Motion in a Straight Line."
        return "\n".join(content)
    else:
        return "No content found for the specified chapter and section."
    
# ---------- Optional PDF extract (pypdf) ----------
PDF_AVAILABLE = False
try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False

def extract_pages_from_pdf(pdf_path: str) -> List[str]:
    """Return list of page texts (1-based order). Empty list if failure."""
    if not PDF_AVAILABLE:
        return []
    try:
        r = PdfReader(pdf_path)
        pages = []
        for p in r.pages:
            t = p.extract_text() or ""
            # Normalize whitespace a bit
            t = re.sub(r"[ \t]+", " ", t).strip()
            pages.append(t)
        return pages
    except Exception:
        return []

# Tool list for easy access
LEARNING_TOOLS = [
    get_course,
    get_section_context, 
    view_progress,
    update_progress,
]