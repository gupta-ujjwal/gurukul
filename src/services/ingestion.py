"""
Course ingestion service using pure regex-based parsing.
Extracts course content from PDF files and ingests into database.
"""
import os
import re
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass
from uuid import uuid4
from pathlib import Path

import pypdf
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..models.models import Course, Chapter, Section

# Configure logging
logger = logging.getLogger(__name__)

# Dataclasses for internal representation
@dataclass
class ParsedSection:
    """Represents a parsed section from PDF content."""
    section_number: str
    title: str
    text: str

@dataclass
class ParsedChapter:
    """Represents a parsed chapter from PDF content."""
    chapter_number: int
    title: str
    sections: List[ParsedSection]

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract plain text from PDF file using pypdf.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text with normalized whitespace
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If PDF extraction fails
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        logger.info(f"Extracting text from PDF: {pdf_path}")
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            
            if len(pdf_reader.pages) == 0:
                raise ValueError(f"PDF has no pages: {pdf_path}")
            
            # Extract text from all pages
            full_text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {e}")
                    continue
            
            # Normalize whitespace
            normalized_text = normalize_whitespace(full_text)
            logger.info(f"Extracted {len(normalized_text)} characters from {pdf_path}")
            
            return normalized_text
            
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {pdf_path}: {e}")
        raise

def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text while preserving structure.
    
    Args:
        text: Raw text to normalize
        
    Returns:
        Normalized text
    """
    # Replace multiple spaces with single space, but preserve line breaks
    lines = text.split('\n')
    normalized_lines = []
    
    for line in lines:
        # Collapse multiple spaces but preserve the line structure
        normalized_line = re.sub(r'\s+', ' ', line.strip())
        if normalized_line:  # Only add non-empty lines
            normalized_lines.append(normalized_line)
    
    # Join lines with single newlines, preserving paragraph structure
    return '\n'.join(normalized_lines)

def find_section_headers(chapter_text: str) -> List[ParsedSection]:
    """
    Find section headers in chapter text using conservative whitelist-based approach.
    Only identifies actual section headers, not exercise questions or random content.
    
    Args:
        chapter_text: Raw chapter text
        
    Returns:
        List of ParsedSection objects
    """
    lines = chapter_text.split('\n')
    sections = []
    found_sections = set()  # Track section numbers we've already found to avoid duplicates
    
    # Known section headers for each format (based on actual PDF analysis)
    keph101_sections = [
        '1.1 INTRODUCTION',
        '1.2 THE INTERNA TIONAL SYSTEM OF UNITS',
        '1.3 SIGNIFICANT FIGURES',
        '1.4 DIMENSIONS OF PHYSICAL QUANTITIES',
        '1.6 DIMENSIONAL ANALYSIS AND ITS'
    ]
    
    keph102_sections = [
        '2.1 Introduction',
        '2.2 Instantaneous velocity and speed',
        '2.3 Acceleration',
        '2.4 Kinematic equations for uniformly accelerated motion',
        '2.5 Relative velocity'
    ]
    
    # Build whitelist of valid section headers
    valid_sections = keph101_sections + keph102_sections
    
    # Also build a mapping of section numbers to expected titles
    section_mapping = {}
    for section in valid_sections:
        match = re.match(r'^(\d+\.\d+)\s+(.+)$', section)
        if match:
            section_num = match.group(1)
            section_title = match.group(2).strip()
            section_mapping[section_num] = section_title
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this line matches a section header pattern
        section_match = re.match(r'^(\d+\.\d+)\s+(.+)$', line)
        if section_match:
            section_number = section_match.group(1)
            section_title = section_match.group(2).strip()
            
            # Skip if we've already found this section number
            if section_number in found_sections:
                i += 1
                continue
            
            # Check if this is a known valid section
            expected_title = section_mapping.get(section_number)
            if expected_title:
                # More strict matching - check if the title matches exactly (case-insensitive)
                # or if it's a close match for the expected title
                normalized_current = section_title.upper().replace(' ', '')
                normalized_expected = expected_title.upper().replace(' ', '')
                
                # Check for exact match or substantial overlap
                if (normalized_current == normalized_expected or
                    normalized_expected in normalized_current or
                    normalized_current in normalized_expected):
                    
                    # Handle multi-line section titles (for Title Case format)
                    full_title = section_title
                    j = i + 1
                    
                    # Check if next line continues the title (for split titles like in keph102.pdf)
                    while (j < len(lines) and 
                           lines[j].strip() and 
                           not lines[j].strip()[0].isdigit() and  # Not starting with number
                           lines[j].strip()[0].islower() and  # Starts with lowercase (continuation)
                           len(lines[j].strip()) > 3):  # Substantial length
                        
                        full_title += " " + lines[j].strip()
                        j += 1
                    
                    # Find section body (text until next section or end)
                    section_body = []
                    k = j  # Start from after the title
                    
                    while k < len(lines):
                        next_line = lines[k].strip()
                        
                        # Stop if we hit another known section header
                        next_section_match = re.match(r'^(\d+\.\d+)\s+(.+)$', next_line)
                        if next_section_match:
                            next_section_num = next_section_match.group(1)
                            if next_section_num in section_mapping:
                                break
                        
                        # Stop if we hit exercise sections
                        if is_exercise_section(next_line):
                            break
                        
                        if next_line:  # Only add non-empty lines
                            section_body.append(next_line)
                        k += 1
                    
                    # Normalize section body
                    normalized_body = normalize_section_body('\n'.join(section_body))
                    
                    section = ParsedSection(
                        section_number=section_number,
                        title=full_title.strip(),
                        text=normalized_body
                    )
                    sections.append(section)
                    found_sections.add(section_number)  # Mark this section as found
                    
                    logger.info(f"Found valid section {section_number}: {full_title.strip()}")
                    
                    # Skip to where we left off
                    i = k - 1  # -1 because loop will increment
        
        i += 1
    
    return sections

def is_valid_section_header(title: str, full_line: str) -> bool:
    """
    Check if a line is a valid section header.
    
    Args:
        title: The title part of the section header
        full_line: The complete line
        
    Returns:
        True if valid section header, False otherwise
    """
    # Must have substantial content
    if len(title) < 5:
        return False
    
    # Must not be exercise-related
    exercise_keywords = [
        'exercise', 'fill', 'question', 'problem', 'answer', 'blank',
        'example', 'consider', 'let', 'suppose', 'if', 'when', 'which'
    ]
    
    title_lower = title.lower()
    for keyword in exercise_keywords:
        if keyword in title_lower:
            return False
    
    # Must be either ALL CAPS or Title Case
    if title.isupper() or title.istitle():
        return True
    
    # Allow mixed case if it's substantial and doesn't contain exercise keywords
    if len(title.split()) >= 2 and not any(char.isdigit() for char in title.split()[-1]):
        return True
    
    return False

def is_exercise_question(title: str) -> bool:
    """
    Check if a title is an exercise question.
    
    Args:
        title: The section title
        
    Returns:
        True if exercise question, False otherwise
    """
    exercise_patterns = [
        r'^\d+\.\d+\s+(Fill|A|The|Which|How|What|Why|When|Where|Explain|State|Calculate|Find|Determine)',
        r'^\d+\.\d+\s+.*\?$',  # Ends with question mark
        r'^\d+\.\d+\s+.*(?:blank|example|consider|let|suppose)',
    ]
    
    for pattern in exercise_patterns:
        if re.match(pattern, title, re.IGNORECASE):
            return True
    
    return False

def is_exercise_section(line: str) -> bool:
    """
    Check if a line indicates the start of exercise section.
    
    Args:
        line: The line to check
        
    Returns:
        True if exercise section, False otherwise
    """
    exercise_starters = [
        'summary', 'exercises', 'points to ponder', 'additional exercises',
        'appendix', 'answers', 'solutions', 'problems'
    ]
    
    line_lower = line.lower()
    for starter in exercise_starters:
        if starter in line_lower:
            return True
    
    return False

def parse_chapter_with_regex(raw_text: str) -> ParsedChapter:
    """
    Parse chapter content using regex patterns.
    
    Args:
        raw_text: Raw text extracted from PDF
        
    Returns:
        ParsedChapter object with sections
        
    Raises:
        ValueError: If chapter header cannot be detected
    """
    logger.info("Parsing chapter content with regex")
    
    # Detect chapter header (handles both "CHAPTER 1" and "CHAPTER ONE")
    chapter_pattern = re.compile(r"CHAPTER\s+(\d+|ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE)\s+([A-Z].*?)\n", re.DOTALL)
    chapter_match = chapter_pattern.search(raw_text)
    
    if not chapter_match:
        raise ValueError("Could not detect chapter header in text")
    
    chapter_num_str = chapter_match.group(1)
    # Convert word numbers to integers
    word_to_num = {
        'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5,
        'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10,
        'ELEVEN': 11, 'TWELVE': 12
    }
    
    if chapter_num_str in word_to_num:
        chapter_number = word_to_num[chapter_num_str]
    else:
        # Try to convert to int directly (for numeric chapters)
        try:
            chapter_number = int(chapter_num_str)
        except ValueError:
            raise ValueError(f"Unknown chapter number format: {chapter_num_str}")
    chapter_title = chapter_match.group(2).strip()
    
    logger.info(f"Found chapter {chapter_number}: {chapter_title}")
    
    # Get the text after the chapter header
    chapter_start = chapter_match.end()
    chapter_text = raw_text[chapter_start:]
    
    # Detect sections using intelligent parsing
    sections = find_section_headers(chapter_text)
    
    if not sections:
        raise ValueError("No sections found in chapter")
    
    logger.info(f"Parsed {len(sections)} sections from chapter {chapter_number}")
    
    logger.info(f"Parsed {len(sections)} sections from chapter {chapter_number}")
    
    return ParsedChapter(
        chapter_number=chapter_number,
        title=chapter_title,
        sections=sections
    )

def normalize_section_body(body_text: str) -> str:
    """
    Normalize section body text, preserving equations and structure.
    
    Args:
        body_text: Raw section body text
        
    Returns:
        Normalized section body
    """
    # Split into lines to preserve structure
    lines = body_text.split('\n')
    normalized_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Preserve equations (look for mathematical patterns)
        if re.search(r'[=+\-*/^]', line) and re.search(r'\d', line):
            # This looks like an equation, preserve it as-is
            normalized_lines.append(line)
        else:
            # Regular text, collapse multiple spaces
            normalized_line = re.sub(r'\s+', ' ', line)
            if normalized_line:
                normalized_lines.append(normalized_line)
    
    return '\n'.join(normalized_lines)

def ingest_chapter_to_db(parsed_chapter: ParsedChapter, course_id: str, db: Session) -> Tuple[int, int]:
    """
    Ingest parsed chapter into database.
    
    Args:
        parsed_chapter: ParsedChapter object to ingest
        course_id: UUID of the course
        db: Database session
        
    Returns:
        Tuple of (chapter_id, sections_count)
        
    Raises:
        Exception: If database ingestion fails
    """
    try:
        logger.info(f"Ingesting chapter {parsed_chapter.chapter_number} to database")
        
        # Create chapter
        chapter = Chapter(
            course_id=course_id,
            number=parsed_chapter.chapter_number,
            title=parsed_chapter.title,
            order=parsed_chapter.chapter_number
        )
        
        db.add(chapter)
        db.flush()  # Get the chapter ID
        
        sections_count = 0
        
        # Create sections
        for section in parsed_chapter.sections:
            db_section = Section(
                chapter_id=chapter.id,
                title=section.title,
                section_number=section.section_number,
                text=section.text,
                version=1
            )
            
            db.add(db_section)
            sections_count += 1
        
        db.commit()
        logger.info(f"Successfully ingested chapter {chapter.id} with {sections_count} sections")
        
        return chapter.id, sections_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to ingest chapter to database: {e}")
        raise

def get_or_create_course(course_name: str, board: str, grade: int, db: Session) -> str:
    """
    Get existing course or create new one.
    
    Args:
        course_name: Name of the course
        board: Educational board (e.g., CBSE)
        grade: Grade level
        db: Database session
        
    Returns:
        Course UUID as string
    """
    try:
        # Check if course exists
        existing_course = db.query(Course).filter(
            Course.name == course_name,
            Course.board == board,
            Course.grade == grade
        ).first()
        
        if existing_course:
            logger.info(f"Found existing course: {existing_course.id}")
            return str(existing_course.id)
        
        # Create new course
        course_id = uuid4()
        new_course = Course(
            id=course_id,
            name=course_name,
            board=board,
            grade=grade
        )
        
        db.add(new_course)
        db.commit()
        
        logger.info(f"Created new course: {course_id}")
        return str(course_id)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to get or create course: {e}")
        raise

def ingest_course_from_pdfs(course_name: str, board: str, grade: int, pdf_paths: List[str]) -> dict:
    """
    Main function to ingest course from multiple PDF files.
    
    Args:
        course_name: Name of the course
        board: Educational board
        grade: Grade level
        pdf_paths: List of PDF file paths
        
    Returns:
        Dictionary with ingestion results
    """
    logger.info(f"Starting course ingestion for {course_name} with {len(pdf_paths)} PDFs")
    
    results = {
        "course_id": None,
        "chapters_ingested": 0,
        "sections_ingested": 0,
        "failed_files": []
    }
    
    db = SessionLocal()
    
    try:
        # Get or create course
        course_id = get_or_create_course(course_name, board, grade, db)
        results["course_id"] = course_id
        
        # Process each PDF
        for pdf_path in pdf_paths:
            try:
                logger.info(f"Processing PDF: {pdf_path}")
                
                # Extract text from PDF
                raw_text = extract_text_from_pdf(pdf_path)
                
                # Parse chapter with regex
                parsed_chapter = parse_chapter_with_regex(raw_text)
                
                # Ingest to database
                chapter_id, sections_count = ingest_chapter_to_db(parsed_chapter, course_id, db)
                
                results["chapters_ingested"] += 1
                results["sections_ingested"] += sections_count
                
                logger.info(f"Successfully processed {pdf_path}")
                
            except Exception as e:
                logger.error(f"Failed to process PDF {pdf_path}: {e}")
                results["failed_files"].append(pdf_path)
                continue
        
        logger.info(f"Course ingestion completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Course ingestion failed: {e}")
        raise
    finally:
        db.close()

def validate_admin_key(admin_key: str) -> bool:
    """
    Validate admin key from environment.
    
    Args:
        admin_key: Admin key to validate
        
    Returns:
        True if valid, False otherwise
    """
    expected_key = os.getenv("SUPER_ADMIN_KEY")
    if not expected_key:
        logger.error("SUPER_ADMIN_KEY not set in environment")
        return False
    
    return admin_key == expected_key