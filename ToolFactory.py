
import os
from jaf import function_tool
from ContextClass import LearningContext
from typing import List
import re  

# ---------------- Tools ----------------
@function_tool 
async def update_progress(context: LearningContext, chapter: str, section: str, score: int) -> str:
    """Update user progress for a chapter and section with a score out of 100."""

    context.progress = context.progress or {}
    context.progress[(chapter, section)] = score
    
    # Simulated progress update
    return f"Progress updated: Chapter '{chapter}', Section '{section}', Score {score}/100."

# ---------------- Tools ----------------
@function_tool 
async def view_progress(context: LearningContext) -> str:
    """View user progress across chapters and sections."""
    
    if not context.progress:
        return "No progress recorded yet."
    
    progress_lines = ["Your Progress:"]
    for (chapter, section), score in context.progress.items():
        progress_lines.append(f"- Chapter: {chapter}, Section: {section}, Score: {score}/100")
    
    return "\n".join(progress_lines)
    

@function_tool
async def get_course(context: LearningContext) -> str:
    """Fetch the course map (chapters and sections)."""
    
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


@function_tool
async def get_section_context(context: LearningContext, chapter: str, section: str) -> str:
    """Fetch content snippets and citations for a chapter and section."""
    
    # Simulated content retrieval
    if chapter == "1" or section == "Units and Measurements":
        content = extract_pages_from_pdf("/Users/Ujjwal.gupta/juspay/Playground/jaf/learning-agent/LerningMaterial/Class 11/Physics/keph101.pdf")
        # print(f"--------- Extracted {len(content)} pages from PDF for Chapter 1.")
        if not content:
            return "No content found for Chapter 1 - Units and Measurements."
        return "\n".join(content)
    elif chapter == "2" or section == "Motion in a Straight Line":
        content = extract_pages_from_pdf("/Users/Ujjwal.gupta/juspay/Playground/jaf/learning-agent/LerningMaterial/Class 11/Physics/keph102.pdf")
        # print(f"----------- Extracted {len(content)} pages from PDF for Chapter 2.")
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