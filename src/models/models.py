"""
SQLAlchemy models for the Learning Agent project.
Uses SQLAlchemy 2.0 style with proper type hints.
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from ..db.database import Base


class Course(Base):
    """Course model representing educational courses."""
    __tablename__ = "courses"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Primary key UUID"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Course name"
    )
    board: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Educational board (e.g., CBSE)"
    )
    grade: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Grade level"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Creation timestamp"
    )

    # Relationships
    chapters: Mapped[list["Chapter"]] = relationship(
        "Chapter",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    progress_records: Mapped[list["Progress"]] = relationship(
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

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    course_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to courses"
    )
    number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Chapter number"
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Chapter title"
    )
    order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Chapter order in course"
    )

    # Relationships
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="chapters"
    )
    sections: Mapped[list["Section"]] = relationship(
        "Section",
        back_populates="chapter",
        cascade="all, delete-orphan"
    )
    progress_records: Mapped[list["Progress"]] = relationship(
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

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    chapter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to chapters"
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Section title"
    )
    section_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Section identifier"
    )
    text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Section content text"
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Content version"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp"
    )

    # Relationships
    chapter: Mapped["Chapter"] = relationship(
        "Chapter",
        back_populates="sections"
    )
    progress_records: Mapped[list["Progress"]] = relationship(
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

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Student full name"
    )
    class_grade: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Grade level (9-12)"
    )
    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Unique username"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hashed password"
    )
    profile_image: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Base64 encoded profile image"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp"
    )

    # Relationships
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    progress_records: Mapped[list["Progress"]] = relationship(
        "Progress",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    study_sessions: Mapped[list["StudySession"]] = relationship(
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

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to students"
    )
    course_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to courses"
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Enrollment timestamp"
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="enrollments"
    )
    course: Mapped["Course"] = relationship(
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

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to students"
    )
    course_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to courses"
    )
    chapter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to chapters"
    )
    section_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to sections"
    )
    completion_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Completion percentage (0-100)"
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last access timestamp"
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="progress_records"
    )
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="progress_records"
    )
    chapter: Mapped["Chapter"] = relationship(
        "Chapter",
        back_populates="progress_records"
    )
    section: Mapped["Section"] = relationship(
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

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to students"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Session start timestamp"
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Session end timestamp"
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Session summary"
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="study_sessions"
    )
    session_events: Mapped[list["SessionEvent"]] = relationship(
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

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Primary key"
    )
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("study_sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to study_sessions"
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Event type (tutor_reply/quiz/answer/feedback)"
    )
    payload_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON payload for event data"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Event timestamp"
    )

    # Relationships
    session: Mapped["StudySession"] = relationship(
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