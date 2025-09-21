#!/usr/bin/env python3
"""
Single database setup script for the Learning Agent project.
This script creates the database and all tables in one operation.
Replaces the entire Alembic migration system with a single file.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.database import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, 
    POSTGRES_USER, POSTGRES_PASSWORD, DATABASE_URL
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create base declarative class
Base = declarative_base()


class Course(Base):
    """Course model representing educational courses."""
    __tablename__ = "courses"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Primary key UUID"
    )
    name = Column(
        String(255),
        nullable=False,
        comment="Course name"
    )
    board = Column(
        String(100),
        nullable=False,
        comment="Educational board (e.g., CBSE)"
    )
    grade = Column(
        Integer,
        nullable=True,
        comment="Grade level"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Creation timestamp"
    )

    # Relationships
    chapters = relationship(
        "Chapter",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    enrollments = relationship(
        "Enrollment",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    progress_records = relationship(
        "Progress",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index('idx_courses_board_grade', 'board', 'grade'),
    )


class Chapter(Base):
    """Chapter model representing course chapters."""
    __tablename__ = "chapters"

    id = Column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to courses"
    )
    number = Column(
        Integer,
        nullable=False,
        comment="Chapter number"
    )
    title = Column(
        String(255),
        nullable=False,
        comment="Chapter title"
    )
    order = Column(
        Integer,
        nullable=False,
        comment="Chapter order in course"
    )

    # Relationships
    course = relationship(
        "Course",
        back_populates="chapters"
    )
    sections = relationship(
        "Section",
        back_populates="chapter",
        cascade="all, delete-orphan"
    )
    progress_records = relationship(
        "Progress",
        back_populates="chapter",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index('idx_chapters_course_id', 'course_id'),
        Index('idx_chapters_course_order', 'course_id', 'order'),
    )


class Section(Base):
    """Section model representing chapter sections."""
    __tablename__ = "sections"

    id = Column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to chapters"
    )
    title = Column(
        String(255),
        nullable=False,
        comment="Section title"
    )
    section_number = Column(
        String(50),
        nullable=False,
        comment="Section identifier"
    )
    text = Column(
        Text,
        nullable=True,
        comment="Section content text"
    )
    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Content version"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp"
    )

    # Relationships
    chapter = relationship(
        "Chapter",
        back_populates="sections"
    )
    progress_records = relationship(
        "Progress",
        back_populates="section",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index('idx_sections_chapter_id', 'chapter_id'),
        Index('idx_sections_chapter_version', 'chapter_id', 'version'),
    )


class Student(Base):
    """Student model representing users."""
    __tablename__ = "students"

    id = Column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    full_name = Column(
        String(255),
        nullable=False,
        comment="Student full name"
    )
    class_grade = Column(
        Integer,
        nullable=False,
        comment="Grade level (9-12)"
    )
    username = Column(
        String(100),
        nullable=False,
        unique=True,
        comment="Unique username"
    )
    hashed_password = Column(
        String(255),
        nullable=False,
        comment="Hashed password"
    )
    profile_image = Column(
        Text,
        nullable=True,
        comment="Base64 encoded profile image"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp"
    )

    # Relationships
    enrollments = relationship(
        "Enrollment",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    progress_records = relationship(
        "Progress",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    study_sessions = relationship(
        "StudySession",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index('idx_students_username', 'username'),
        Index('idx_students_class_grade', 'class_grade'),
    )


class Enrollment(Base):
    """Enrollment model representing student course enrollments."""
    __tablename__ = "enrollments"

    id = Column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to students"
    )
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to courses"
    )
    enrolled_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Enrollment timestamp"
    )

    # Relationships
    student = relationship(
        "Student",
        back_populates="enrollments"
    )
    course = relationship(
        "Course",
        back_populates="enrollments"
    )

    # Indexes
    __table_args__ = (
        Index('idx_enrollments_student_id', 'student_id'),
        Index('idx_enrollments_course_id', 'course_id'),
        Index('idx_enrollments_student_course', 'student_id', 'course_id'),
    )


class Progress(Base):
    """Progress model tracking student learning progress."""
    __tablename__ = "progress"

    id = Column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to students"
    )
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to courses"
    )
    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to chapters"
    )
    section_id = Column(
        Integer,
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to sections"
    )
    completion_percent = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Completion percentage (0-100)"
    )
    last_accessed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last access timestamp"
    )

    # Relationships
    student = relationship(
        "Student",
        back_populates="progress_records"
    )
    course = relationship(
        "Course",
        back_populates="progress_records"
    )
    chapter = relationship(
        "Chapter",
        back_populates="progress_records"
    )
    section = relationship(
        "Section",
        back_populates="progress_records"
    )

    # Indexes
    __table_args__ = (
        Index('idx_progress_student_id', 'student_id'),
        Index('idx_progress_course_id', 'course_id'),
        Index('idx_progress_chapter_id', 'chapter_id'),
        Index('idx_progress_section_id', 'section_id'),
        Index('idx_progress_student_course', 'student_id', 'course_id'),
        Index('idx_progress_student_chapter', 'student_id', 'chapter_id'),
    )


class StudySession(Base):
    """StudySession model tracking learning sessions."""
    __tablename__ = "study_sessions"

    id = Column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to students"
    )
    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Session start timestamp"
    )
    ended_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Session end timestamp"
    )
    summary = Column(
        Text,
        nullable=True,
        comment="Session summary"
    )

    # Relationships
    student = relationship(
        "Student",
        back_populates="study_sessions"
    )
    session_events = relationship(
        "SessionEvent",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index('idx_study_sessions_student_id', 'student_id'),
        Index('idx_study_sessions_started_at', 'started_at'),
    )


class SessionEvent(Base):
    """SessionEvent model tracking events within study sessions."""
    __tablename__ = "session_events"

    id = Column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    session_id = Column(
        Integer,
        ForeignKey("study_sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to study_sessions"
    )
    event_type = Column(
        String(50),
        nullable=False,
        comment="Event type (tutor_reply/quiz/answer/feedback)"
    )
    payload_json = Column(
        Text,
        nullable=True,
        comment="JSON payload for event data"
    )
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Event timestamp"
    )

    # Relationships
    session = relationship(
        "StudySession",
        back_populates="session_events"
    )

    # Indexes
    __table_args__ = (
        Index('idx_session_events_session_id', 'session_id'),
        Index('idx_session_events_event_type', 'event_type'),
        Index('idx_session_events_timestamp', 'timestamp'),
        Index('idx_session_events_session_type', 'session_id', 'event_type'),
    )


def get_admin_connection():
    """Get a connection to PostgreSQL admin database."""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database="postgres",  # Connect to admin database
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise


def database_exists(conn, db_name):
    """Check if a database exists."""
    with conn.cursor() as cursor:
        cursor.execute(
            sql.SQL("SELECT 1 FROM pg_database WHERE datname = {}").format(
                sql.Literal(db_name)
            )
        )
        return cursor.fetchone() is not None


def create_database(conn, db_name):
    """Create the specified database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(db_name)
                )
            )
        logger.info(f"Database '{db_name}' created successfully")
    except psycopg2.Error as e:
        logger.error(f"Failed to create database '{db_name}': {e}")
        raise


def setup_database():
    """Main function to setup the database and all tables."""
    logger.info("Starting database setup process...")
    
    try:
        # Step 1: Create database if it doesn't exist
        admin_conn = get_admin_connection()
        
        if not database_exists(admin_conn, POSTGRES_DB):
            logger.info(f"Database '{POSTGRES_DB}' does not exist, creating it...")
            create_database(admin_conn, POSTGRES_DB)
        else:
            logger.info(f"Database '{POSTGRES_DB}' already exists")
        
        admin_conn.close()
        
        # Step 2: Create all tables
        logger.info("Creating database tables...")
        engine = create_engine(DATABASE_URL)
        logger.info(f"Connected to database: {DATABASE_URL}")
        
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("All tables created successfully")
        
        # Log table information
        logger.info("Created tables:")
        for table_name in Base.metadata.tables.keys():
            logger.info(f"  - {table_name}")
        
        logger.info("Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False


def verify_database():
    """Verify that all tables were created correctly."""
    logger.info("Verifying database structure...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Check if all tables exist
        expected_tables = {
            'courses', 'chapters', 'sections', 'students', 
            'enrollments', 'progress', 'study_sessions', 'session_events'
        }
        
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT table_name FROM information_schema.tables "
                     "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
            )
            existing_tables = {row[0] for row in result}
        
        missing_tables = expected_tables - existing_tables
        if missing_tables:
            logger.error(f"Missing tables: {missing_tables}")
            return False
        
        logger.info("All expected tables found")
        
        # Check indexes
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
            )
            indexes = {row[0] for row in result}
        
        expected_indexes = {
            'idx_courses_board_grade',
            'idx_chapters_course_id', 'idx_chapters_course_order',
            'idx_sections_chapter_id', 'idx_sections_chapter_version',
            'idx_students_username', 'idx_students_class_grade',
            'idx_enrollments_student_id', 'idx_enrollments_course_id', 'idx_enrollments_student_course',
            'idx_progress_student_id', 'idx_progress_course_id', 'idx_progress_chapter_id',
            'idx_progress_section_id', 'idx_progress_student_course', 'idx_progress_student_chapter',
            'idx_study_sessions_student_id', 'idx_study_sessions_started_at',
            'idx_session_events_session_id', 'idx_session_events_event_type',
            'idx_session_events_timestamp', 'idx_session_events_session_type'
        }
        
        missing_indexes = expected_indexes - indexes
        if missing_indexes:
            logger.warning(f"Missing indexes: {missing_indexes}")
        
        logger.info("Database verification completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Setup the Learning Agent database')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    print("Learning Agent Database Setup Script")
    print("==================================")
    print(f"Database: {POSTGRES_DB}")
    print(f"Host: {POSTGRES_HOST}:{POSTGRES_PORT}")
    print(f"User: {POSTGRES_USER}")
    print()
    
    # Confirm with user unless --force is used
    if not args.force:
        response = input("This will setup the database with all tables. Are you sure? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Operation cancelled.")
            sys.exit(0)
    
    # Setup database
    success = setup_database()
    
    if success:
        # Verify database
        verify_success = verify_database()
        
        if verify_success:
            print("\n✅ Database setup completed successfully!")
            print("All tables and indexes have been created.")
        else:
            print("\n⚠️  Database setup completed but verification failed.")
            print("Please check the logs for details.")
    else:
        print("\n❌ Database setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()