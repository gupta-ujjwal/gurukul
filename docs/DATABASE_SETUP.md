# Database Setup Guide

This guide explains how to set up and initialize the database for the Learning Agent project using the new consolidated scripts.

## Overview

The Learning Agent project now uses a simplified database initialization approach with two main scripts:

1. **`scripts/cleanup_database.py`** - Drops and recreates the database
2. **`scripts/initialize_database.py`** - Creates all tables and indexes

This replaces the previous Alembic-based migration system with a single, comprehensive initialization script.

## Prerequisites

- PostgreSQL server running locally or accessible
- Python 3.8+ with virtual environment
- Database credentials configured in `.env` file

## Environment Configuration

Ensure your `.env` file contains the following database configuration:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=learning_agent
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
```

## Database Setup Process

### Step 1: Activate Virtual Environment

```bash
source .venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Clean Up Existing Database (Optional)

If you want to start with a fresh database, run the cleanup script:

```bash
python scripts/cleanup_database.py
```

This will:
- Connect to PostgreSQL as the admin user
- Drop the existing `learning_agent` database if it exists
- Create a fresh, empty database

**⚠️ Warning:** This operation will delete all existing data in the database.

### Step 4: Initialize Database

Run the initialization script to create all tables and indexes:

```bash
python scripts/initialize_database.py
```

For automated deployments, use the `--force` flag to skip confirmation:

```bash
python scripts/initialize_database.py --force
```

## Database Schema

The initialization script creates the following tables:

### Core Tables

1. **`courses`** - Educational courses
   - UUID primary key
   - Course name, board, grade
   - Created timestamp

2. **`chapters`** - Course chapters
   - Integer primary key
   - Foreign key to courses
   - Chapter number, title, order

3. **`sections`** - Chapter sections
   - Integer primary key
   - Foreign key to chapters
   - Section title, number, content text
   - Version tracking

### User Management

4. **`students`** - User accounts
   - Integer primary key
   - User profile information
   - Authentication credentials
   - Profile image support

### Relationships

5. **`enrollments`** - Student course enrollments
   - Many-to-many relationship between students and courses
   - Enrollment timestamp

6. **`progress`** - Learning progress tracking
   - Student progress per course, chapter, and section
   - Completion percentage
   - Last access timestamp

### Session Tracking

7. **`study_sessions`** - Learning sessions
   - Session start/end times
   - Session summary

8. **`session_events`** - Events within sessions
   - Event types (tutor_reply, quiz, answer, feedback)
   - JSON payload for event data
   - Event timestamps

## Database Indexes

The script creates the following indexes for performance optimization:

### Course Indexes
- `idx_courses_board_grade` - Composite index on board and grade

### Chapter Indexes
- `idx_chapters_course_id` - Foreign key index
- `idx_chapters_course_order` - Composite index for ordering

### Section Indexes
- `idx_sections_chapter_id` - Foreign key index
- `idx_sections_chapter_version` - Version tracking index

### Student Indexes
- `idx_students_username` - Unique username index
- `idx_students_class_grade` - Grade filtering index

### Enrollment Indexes
- `idx_enrollments_student_id` - Foreign key index
- `idx_enrollments_course_id` - Foreign key index
- `idx_enrollments_student_course` - Composite index

### Progress Indexes
- `idx_progress_student_id` - Foreign key index
- `idx_progress_course_id` - Foreign key index
- `idx_progress_chapter_id` - Foreign key index
- `idx_progress_section_id` - Foreign key index
- `idx_progress_student_course` - Composite index
- `idx_progress_student_chapter` - Composite index

### Session Indexes
- `idx_study_sessions_student_id` - Foreign key index
- `idx_study_sessions_started_at` - Time-based index
- `idx_session_events_session_id` - Foreign key index
- `idx_session_events_event_type` - Event type index
- `idx_session_events_timestamp` - Time-based index
- `idx_session_events_session_type` - Composite index

## Migration from Alembic

### Previous System
- Used Alembic for database migrations
- Multiple migration files in `migrations/versions/`
- Complex versioning and downgrade capabilities

### New System
- Single initialization script
- All schema defined in one place
- Simpler deployment and maintenance
- No version tracking needed for initial setup

### Benefits
- **Simplicity**: Single script instead of multiple migration files
- **Clarity**: All schema definitions in one location
- **Performance**: No migration version overhead
- **Reliability**: Consistent database state every time
- **Maintenance**: Easier to understand and modify

## Common Operations

### Reset Database

To completely reset the database:

```bash
# Clean up existing database
python scripts/cleanup_database.py

# Initialize fresh database
python scripts/initialize_database.py --force
```

### Verify Database Setup

To verify that the database was set up correctly:

```bash
python scripts/initialize_database.py --force
```

The script will automatically verify that all tables and indexes were created correctly.

### Development Workflow

1. **Initial Setup**: Run cleanup and initialization scripts
2. **Schema Changes**: Modify the `initialize_database.py` script
3. **Apply Changes**: Run the initialization script again
4. **Data Migration**: Manually migrate data if needed (rare for development)

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Ensure PostgreSQL is running
   - Check database credentials in `.env`
   - Verify network connectivity

2. **Permission Errors**
   - Ensure the database user has CREATE DATABASE privileges
   - Check that the user can connect to the PostgreSQL server

3. **Missing Dependencies**
   - Activate virtual environment: `source .venv/bin/activate`
   - Install requirements: `pip install -r requirements.txt`

4. **Database Already Exists**
   - Use the cleanup script to drop and recreate the database
   - Or manually drop the database in PostgreSQL

### Debug Mode

For detailed logging, you can modify the script to set the logging level to DEBUG:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Integration with Application

The database initialization scripts are designed to work seamlessly with the existing application:

- **Models**: The script uses the same table definitions as the SQLAlchemy models
- **Connections**: Uses the same database URL configuration
- **Compatibility**: Fully compatible with existing application code

## Automated Deployment

For CI/CD pipelines, you can use the scripts with the `--force` flag:

```bash
# Example deployment script
#!/bin/bash
set -e

source .venv/bin/activate

# Clean up database
python scripts/cleanup_database.py --force

# Initialize database
python scripts/initialize_database.py --force

echo "Database setup completed successfully!"
```

## Security Considerations

- **Database Credentials**: Store sensitive credentials in environment variables
- **Backup**: Always backup production data before running cleanup scripts
- **Access Control**: Limit database user privileges to what's necessary
- **Network Security**: Ensure database connections are secure (use SSL in production)

## Future Enhancements

Potential improvements for the database setup:

1. **Data Seeding**: Add option to populate initial data
2. **Environment-specific Configurations**: Support different environments (dev, staging, prod)
3. **Backup Integration**: Automatic backup before cleanup operations
4. **Validation Scripts**: More comprehensive data validation
5. **Performance Monitoring**: Database performance metrics collection

## Support

If you encounter any issues with the database setup:

1. Check the logs for detailed error messages
2. Verify your PostgreSQL installation and configuration
3. Ensure all dependencies are properly installed
4. Review the environment configuration
5. Check PostgreSQL server logs for connection issues