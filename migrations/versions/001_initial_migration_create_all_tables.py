"""Initial migration - create all tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for the learning agent database."""
    
    # Create courses table
    op.create_table(
        'courses',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('board', sa.String(length=100), nullable=False),
        sa.Column('grade', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='Course model representing educational courses'
    )
    op.create_index('idx_courses_board_grade', 'courses', ['board', 'grade'], unique=False)
    
    # Create chapters table
    op.create_table(
        'chapters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Chapter model representing course chapters'
    )
    op.create_index('idx_chapters_course_id', 'chapters', ['course_id'], unique=False)
    op.create_index('idx_chapters_course_order', 'chapters', ['course_id', 'order'], unique=False)
    
    # Create sections table
    op.create_table(
        'sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('section_number', sa.String(length=50), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Section model representing chapter sections'
    )
    op.create_index('idx_sections_chapter_id', 'sections', ['chapter_id'], unique=False)
    op.create_index('idx_sections_chapter_version', 'sections', ['chapter_id', 'version'], unique=False)
    
    # Create students table
    op.create_table(
        'students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('class_grade', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('profile_image', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        comment='Student model representing users'
    )
    op.create_index('idx_students_username', 'students', ['username'], unique=True)
    op.create_index('idx_students_class_grade', 'students', ['class_grade'], unique=False)
    
    # Create enrollments table
    op.create_table(
        'enrollments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Enrollment model representing student course enrollments'
    )
    op.create_index('idx_enrollments_student_id', 'enrollments', ['student_id'], unique=False)
    op.create_index('idx_enrollments_course_id', 'enrollments', ['course_id'], unique=False)
    op.create_index('idx_enrollments_student_course', 'enrollments', ['student_id', 'course_id'], unique=False)
    
    # Create progress table
    op.create_table(
        'progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('section_id', sa.Integer(), nullable=False),
        sa.Column('completion_percent', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Progress model tracking student learning progress'
    )
    op.create_index('idx_progress_student_id', 'progress', ['student_id'], unique=False)
    op.create_index('idx_progress_course_id', 'progress', ['course_id'], unique=False)
    op.create_index('idx_progress_chapter_id', 'progress', ['chapter_id'], unique=False)
    op.create_index('idx_progress_section_id', 'progress', ['section_id'], unique=False)
    op.create_index('idx_progress_student_course', 'progress', ['student_id', 'course_id'], unique=False)
    op.create_index('idx_progress_student_chapter', 'progress', ['student_id', 'chapter_id'], unique=False)
    
    # Create study_sessions table
    op.create_table(
        'study_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='StudySession model tracking learning sessions'
    )
    op.create_index('idx_study_sessions_student_id', 'study_sessions', ['student_id'], unique=False)
    op.create_index('idx_study_sessions_started_at', 'study_sessions', ['started_at'], unique=False)
    
    # Create session_events table
    op.create_table(
        'session_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['study_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='SessionEvent model tracking events within study sessions'
    )
    op.create_index('idx_session_events_session_id', 'session_events', ['session_id'], unique=False)
    op.create_index('idx_session_events_event_type', 'session_events', ['event_type'], unique=False)
    op.create_index('idx_session_events_timestamp', 'session_events', ['timestamp'], unique=False)
    op.create_index('idx_session_events_session_type', 'session_events', ['session_id', 'event_type'], unique=False)


def downgrade() -> None:
    """Drop all tables in reverse order."""
    
    # Drop session_events table
    op.drop_index('idx_session_events_session_type', table_name='session_events')
    op.drop_index('idx_session_events_timestamp', table_name='session_events')
    op.drop_index('idx_session_events_event_type', table_name='session_events')
    op.drop_index('idx_session_events_session_id', table_name='session_events')
    op.drop_table('session_events')
    
    # Drop study_sessions table
    op.drop_index('idx_study_sessions_started_at', table_name='study_sessions')
    op.drop_index('idx_study_sessions_student_id', table_name='study_sessions')
    op.drop_table('study_sessions')
    
    # Drop progress table
    op.drop_index('idx_progress_student_chapter', table_name='progress')
    op.drop_index('idx_progress_student_course', table_name='progress')
    op.drop_index('idx_progress_section_id', table_name='progress')
    op.drop_index('idx_progress_chapter_id', table_name='progress')
    op.drop_index('idx_progress_course_id', table_name='progress')
    op.drop_index('idx_progress_student_id', table_name='progress')
    op.drop_table('progress')
    
    # Drop enrollments table
    op.drop_index('idx_enrollments_student_course', table_name='enrollments')
    op.drop_index('idx_enrollments_course_id', table_name='enrollments')
    op.drop_index('idx_enrollments_student_id', table_name='enrollments')
    op.drop_table('enrollments')
    
    # Drop students table
    op.drop_index('idx_students_class_grade', table_name='students')
    op.drop_index('idx_students_username', table_name='students')
    op.drop_table('students')
    
    # Drop sections table
    op.drop_index('idx_sections_chapter_version', table_name='sections')
    op.drop_index('idx_sections_chapter_id', table_name='sections')
    op.drop_table('sections')
    
    # Drop chapters table
    op.drop_index('idx_chapters_course_order', table_name='chapters')
    op.drop_index('idx_chapters_course_id', table_name='chapters')
    op.drop_table('chapters')
    
    # Drop courses table
    op.drop_index('idx_courses_board_grade', table_name='courses')
    op.drop_table('courses')