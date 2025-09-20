import os
from langchain_core.tools import tool
from ContextClass import LearningContext, LearningState
from typing import List
import re
from config.database import get_db
from models import Student, Progress, Course, Section, Chapter
from sqlalchemy.orm import Session
import logging

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
    """Fetch the course map showing available chapters and sections from the database."""
    db_generator = get_db()
    db = next(db_generator)
    try:
        # Get all courses from database
        courses = db.query(Course).all()
        
        if not courses:
            return "No courses found in the database. Please contact your administrator to set up course content."
        
        course_lines = []
        for course in courses:
            course_lines.append(f"Course: {course.name} (Class {course.grade})")
            
            # Get chapters for this course, then sections
            chapters = db.query(Chapter).filter(Chapter.course_id == course.id).order_by(Chapter.order).all()
            
            for chapter in chapters:
                course_lines.append(f"    Chapter {chapter.number} – {chapter.title}")
                
                # Get sections for this chapter
                sections = db.query(Section).filter(Section.chapter_id == chapter.id).order_by(Section.section_number).all()
                for section in sections:
                    course_lines.append(f"        {section.section_number}. {section.title}")
                    if section.text:
                        # Show first 100 chars of section text as description
                        desc = section.text[:100] + "..." if len(section.text) > 100 else section.text
                        course_lines.append(f"            {desc}")
        
        return "\n".join(course_lines)
        
    except Exception as e:
        logging.error(f"Error fetching course: {str(e)}")
        return "Error fetching course data."
    finally:
        # Let the generator handle closing the session
        try:
            next(db_generator)
        except StopIteration:
            pass

@tool
def get_section_context(chapter: str, section: str) -> str:
    """Fetch content snippets and citations for a specific chapter and section from the database.
    
    Args:
        chapter: The chapter name or number
        section: The section name
    """
    db_generator = get_db()
    db = next(db_generator)
    try:
        # Try to find section by chapter number and section title/number
        section_query = db.query(Section).join(Chapter).join(Course)
        
        # Try to match by chapter number
        if chapter.isdigit():
            section_query = section_query.filter(Chapter.number == int(chapter))
        else:
            # Try to match by chapter title
            section_query = section_query.filter(Chapter.title.ilike(f"%{chapter}%"))
        
        # Try to match by section
        if section.isdigit():
            section_query = section_query.filter(Section.section_number == section)
        else:
            section_query = section_query.filter(Section.title.ilike(f"%{section}%"))
        
        db_section = section_query.first()
        
        if db_section:
            # Get chapter title through relationship
            chapter_title = db_section.chapter.title if db_section.chapter else "Unknown Chapter"
            
            # Use section text content if available
            if db_section.text:
                return f"Content for {chapter_title} - {db_section.title}:\n\n{db_section.text[:1000]}..."  # First 1000 characters
            
            return f"Found section: {chapter_title} - {db_section.title}, but no detailed content available."
        
        return "No content found for the specified chapter and section. Please ensure the course content is properly set up in the database."
            
    except Exception as e:
        logging.error(f"Error fetching section context: {str(e)}")
        return "Error fetching section content."
    finally:
        # Let the generator handle closing the session
        try:
            next(db_generator)
        except StopIteration:
            pass
    
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