# Learning Agent Codebase Reference

## Project Overview

This is a comprehensive reference document for the Learning Agent project - a web-based AI-powered educational platform designed to help students learn CBSE Class 11 Physics through interactive chat sessions, progress tracking, and personalized learning paths.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Core Components](#core-components)
3. [Database Layer](#database-layer)
4. [API Layer](#api-layer)
5. [Agent System](#agent-system)
6. [Tools System](#tools-system)
7. [Utilities](#utilities)
8. [Web Interface](#web-interface)
9. [Testing](#testing)
10. [Dependencies](#dependencies)
11. [Environment Configuration](#environment-configuration)
12. [Key Features](#key-features)
13. [Architecture Patterns](#architecture-patterns)

## Project Structure

```
learning-agent/
├── main.py                           # CLI entry point
├── requirements.txt                  # Python dependencies
├── README.md                         # Project documentation
├── run.sh                           # Unix startup script
├── shell.nix                        # Nix shell configuration
├── .env                             # Environment variables
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── LICENSE                          # License file
├── src/
│   ├── __init__.py                  # Package initialization
│   ├── db/                          # Database layer
│   │   ├── __init__.py
│   │   └── database.py              # Database configuration and session management
│   ├── models/                      # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── models.py                # Database table definitions
│   ├── apis/                        # API layer
│   │   ├── __init__.py
│   │   └── app.py                   # Flask application with WebSocket support
│   ├── agents/                      # AI agent system
│   │   ├── __init__.py
│   │   ├── ContextClass.py          # Learning context management
│   │   ├── AgentFactory.py          # LangGraph agent creation
│   │   └── prompts/                 # Agent prompts (empty)
│   │       └── __init__.py
│   ├── tools/                       # Agent tools
│   │   ├── __init__.py
│   │   └── ToolFactory.py           # Tool definitions and factory
│   └── utils/                       # Utility functions
│       ├── __init__.py
│       └── auth.py                  # Authentication utilities
├── web/                            # Web interface
│   ├── templates/                   # HTML templates
│   │   ├── index.html               # Main chat interface
│   │   └── auth.html                # Login/signup interface
│   └── static/                      # Static assets
│       ├── css/
│       │   └── style.css            # Main stylesheet
│       └── js/
│           └── script.js            # Client-side JavaScript
├── tests/                          # Test files
│   ├── __init__.py
│   ├── test_tools.py               # Tool integration tests
│   └── test_websocket.py           # WebSocket connection tests
├── migrations/                     # Database migrations
│   ├── alembic.ini                 # Alembic configuration
│   ├── env.py                      # Migration environment
│   └── versions/
│       └── 001_initial_migration_create_all_tables.py  # Initial database schema
├── learning_materials/             # Educational content
│   └── Class 11/
│       └── Physics/
│           ├── keph101.pdf          # Physics textbook chapter 1
│           └── keph102.pdf          # Physics textbook chapter 2
└── venv/                          # Virtual environment (excluded from git)
```

## Core Components

### Main Application Entry Points

#### `main.py` (main.py:1-67)
- **Purpose**: CLI interface for the learning agent
- **Key Functions**:
  - `get_cli_context()`: Creates temporary learning context for CLI usage
  - `interactive_learning_agent()`: REPL interface for LangGraph agent
- **Features**: 
  - Interactive chat loop with quit/exit commands
  - Temporary session management (data not persisted)
  - Error handling for agent execution

#### `src/apis/app.py` (src/apis/app.py:1-578)
- **Purpose**: Main Flask web application with WebSocket support
- **Key Components**:
  - Flask app initialization with SocketIO
  - Authentication routes (login, signup, logout)
  - WebSocket event handlers
  - Progress tracking API endpoints
  - Profile management
- **Features**:
  - Real-time chat via WebSockets
  - User authentication with session management
  - Progress tracking and updates
  - Profile image upload
  - Markdown to HTML conversion

## Database Layer

### Database Configuration (`src/db/database.py`)

#### Connection Setup (src/db/database.py:12-25)
```python
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "learning_agent")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
```

#### Database Engine (src/db/database.py:28-35)
- SQLAlchemy engine with connection pooling
- `pool_pre_ping=True`: Connection health checks
- `pool_recycle=300`: Connection recycling every 5 minutes
- Session management with `SessionLocal`

### Database Models (`src/models/models.py`)

#### Course Model (src/models/models.py:18-67)
- **Fields**: id (UUID), name, board, grade, created_at
- **Relationships**: chapters, enrollments, progress_records
- **Indexes**: idx_courses_board_grade

#### Chapter Model (src/models/models.py:70-115)
- **Fields**: id, course_id (UUID), number, title, order
- **Relationships**: course, sections, progress_records
- **Indexes**: idx_chapters_course_id, idx_chapters_course_order

#### Section Model (src/models/models.py:118-170)
- **Fields**: id, chapter_id, title, section_number, text, version, updated_at
- **Relationships**: chapter, progress_records
- **Indexes**: idx_sections_chapter_id, idx_sections_chapter_version

#### Student Model (src/models/models.py:173-233)
- **Fields**: id, full_name, class_grade, username, hashed_password, profile_image, created_at, updated_at
- **Relationships**: enrollments, progress_records, study_sessions
- **Indexes**: idx_students_username, idx_students_class_grade

#### Enrollment Model (src/models/models.py:236-269)
- **Fields**: id, student_id, course_id (UUID), enrolled_at
- **Relationships**: student, course
- **Indexes**: idx_enrollments_student_id, idx_enrollments_course_id, idx_enrollments_student_course

#### Progress Model (src/models/models.py:272-335)
- **Fields**: id, student_id, course_id (UUID), chapter_id, section_id, completion_percent, last_accessed_at
- **Relationships**: student, course, chapter, section
- **Indexes**: Multiple composite indexes for performance

#### StudySession Model (src/models/models.py:338-376)
- **Fields**: id, student_id, started_at, ended_at, summary
- **Relationships**: student, session_events
- **Indexes**: idx_study_sessions_student_id, idx_study_sessions_started_at

#### SessionEvent Model (src/models/models.py:379-423)
- **Fields**: id, session_id, event_type, payload_json, timestamp
- **Relationships**: session
- **Indexes**: idx_session_events_session_id, idx_session_events_event_type, idx_session_events_timestamp

### Database Migrations

#### Initial Migration (`migrations/versions/001_initial_migration_create_all_tables.py`)
- Creates all database tables with proper relationships
- Implements foreign key constraints with CASCADE deletion
- Sets up performance indexes
- Uses PostgreSQL UUID generation for course IDs

## API Layer

### Authentication Routes

#### Signup (`src/apis/app.py:88-140`)
- **Endpoint**: `POST /signup`
- **Validation**: Name, class (9-12), username, password strength
- **Features**: Password hashing, username uniqueness check
- **Response**: JSON with success/failure status

#### Login (`src/apis/app.py:142-194`)
- **Endpoint**: `POST /login`
- **Validation**: Username and password verification
- **Features**: Session creation, last login timestamp update
- **Response**: JSON with user data and session info

#### Logout (`src/apis/app.py:196-198`)
- **Endpoint**: `GET /logout`
- **Action**: Clears session data

### Progress API

#### Get Progress (`src/apis/app.py:207-276`)
- **Endpoint**: `GET /api/progress`
- **Features**: Calculates overall progress, topics covered, last accessed chapter
- **Response**: JSON with progress metrics

#### Update Progress (`src/apis/app.py:278-351`)
- **Endpoint**: `POST /api/progress`
- **Validation**: Course, chapter, section IDs, completion percentage (0-100)
- **Features**: Creates or updates progress records
- **Response**: JSON with updated progress

### Profile API

#### Get Profile (`src/apis/app.py:353-393`)
- **Endpoint**: `GET /api/profile`
- **Features**: Returns user profile data including profile image
- **Response**: JSON with profile information

#### Update Profile Image (`src/apis/app.py:395-447`)
- **Endpoint**: `POST /api/profile/image`
- **Validation**: Base64 image format, size limits (1MB)
- **Features**: Profile image upload and storage
- **Response**: JSON with updated profile image

### WebSocket Events

#### Connection Events (`src/apis/app.py:450-458`)
- `connect`: Logs client connection, sends welcome message
- `disconnect`: Logs client disconnection

#### Message Handling (`src/apis/app.py:460-481`)
- `message`: Processes user messages, validates input, starts background task
- Features: User context validation, async message processing

#### Message Processing (`src/apis/app.py:483-577`)
- `run_async_message`: Wrapper for async message processing
- `process_message`: Core message processing with LangGraph agent
- `convert_markdown_to_html`: Converts agent responses to clean HTML

## Agent System

### Learning Context (`src/agents/ContextClass.py`)

#### LangGraph State (src/agents/ContextClass.py:12-17)
```python
class LearningState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    learning_context: "LearningContext"
```

#### LearningContext Class (src/agents/ContextClass.py:20-85)
- **Purpose**: Manages user learning session data
- **Fields**: user_id, session_id, created_at, progress, past_messages
- **Key Methods**:
  - `add_message()`: Adds messages to conversation history
  - `get_messages_as_langchain()`: Converts to LangChain format
  - `update_progress()`: Updates progress in database
  - `get_progress_summary()`: Returns formatted progress summary

### Agent Factory (`src/agents/AgentFactory.py`)

#### Agent Creation (src/agents/AgentFactory.py:12-89)
- **LLM Integration**: Uses ChatLiteLLM with configurable model
- **System Instructions**: Comprehensive tutoring guidelines for CBSE Physics
- **Tool Binding**: Binds learning tools to LLM
- **Graph Workflow**: StateGraph with agent and tools nodes

#### Agent Execution (src/agents/AgentFactory.py:92-147)
- `run_learning_agent()`: Synchronous agent execution
- `run_learning_agent_async()`: Asynchronous agent execution
- Features: Context management, conversation history, error handling

## Tools System

### Tool Factory (`src/tools/ToolFactory.py`)

#### Context Management (src/tools/ToolFactory.py:12-25)
- Global context reference for tool access
- `set_current_context()`: Sets active learning context
- `get_current_context()`: Retrieves current context

#### Learning Tools

##### get_course Tool (src/tools/ToolFactory.py:58-100)
- **Purpose**: Fetches course structure from database
- **Returns**: Formatted course map with chapters and sections
- **Features**: Hierarchical display, content descriptions

##### get_section_context Tool (src/tools/ToolFactory.py:102-150)
- **Purpose**: Fetches specific section content
- **Parameters**: chapter, section (flexible matching)
- **Returns**: Section content with chapter context
- **Features**: Content truncation, error handling

##### view_progress Tool (src/tools/ToolFactory.py:43-56)
- **Purpose**: Displays user progress summary
- **Returns**: Formatted progress information
- **Features**: Memory-based progress tracking

##### update_progress Tool (src/tools/ToolFactory.py:28-41)
- **Purpose**: Updates user progress for chapters/sections
- **Parameters**: chapter, section, score (0-100)
- **Returns**: Confirmation message
- **Features**: Database integration, validation

#### PDF Processing (src/tools/ToolFactory.py:152-170)
- Optional PDF extraction using pypdf
- `extract_pages_from_pdf()`: Returns list of page texts
- Graceful fallback when PDF unavailable

## Utilities

### Authentication Utilities (`src/utils/auth.py`)

#### Password Management (src/utils/auth.py:12-35)
- `verify_password()`: Verifies plain password against hash
- `get_password_hash()`: Hashes password using bcrypt
- **Configuration**: bcrypt with 12 rounds for security

#### Password Generation (src/utils/auth.py:38-47)
- `generate_secure_password()`: Generates random secure passwords
- **Features**: Configurable length, character variety

#### Password Strength Validation (src/utils/auth.py:50-70)
- `is_password_strong()`: Validates password strength
- **Requirements**: 8+ chars, uppercase, lowercase, digit, special character
- **Returns**: Tuple of (is_strong, message)

## Web Interface

### HTML Templates

#### Main Chat Interface (`web/templates/index.html`)
- **Layout**: Sidebar + main chat area
- **Sidebar Components**:
  - User profile with image upload
  - Subject selection (Physics, Chemistry, Math, Biology)
  - Class selection (9-12)
  - Progress tracking cards
- **Chat Area**:
  - Header with agent info
  - Message display area
  - Suggested questions
  - Input form with send button
- **Features**: Responsive design, modern UI, WebSocket integration

#### Authentication Interface (`web/templates/auth.html`)
- **Layout**: Split design with marketing copy + forms
- **Features**:
  - Tabbed login/signup interface
  - Form validation
  - Error handling with alerts
  - Responsive design
- **Styling**: Gradient backgrounds, modern form elements

### Client-Side JavaScript (`web/static/js/script.js`)

#### Core Functionality (web/static/js/script.js:1-50)
- DOM element initialization
- UI interaction setup
- Profile editing functionality
- Progress data loading
- User profile loading

#### WebSocket Management (web/static/js/script.js:52-150)
- Socket.io connection with error handling
- Connection timeout and retry logic
- Message sending and receiving
- Typing indicators
- System messages for connection status

#### Message Processing (web/static/js/script.js:152-250)
- `sendMessage()`: Handles user message submission
- `addMessage()`: Adds messages to chat interface
- `showSystemMessage()`: Displays system notifications
- `formatAgentMessage()`: Converts agent responses to HTML
- `escapeHtml()`: HTML escaping for security

#### UI Interactions (web/static/js/script.js:252-350)
- Subject and class selection
- Suggestion button handling
- Sidebar toggle functionality
- Chat clearing with confirmation
- Keyboard shortcuts (Ctrl+K, Escape)

#### Progress and Profile (web/static/js/script.js:352-450)
- `loadUserProgress()`: Fetches and displays progress
- `updateUserProgress()`: Updates progress metrics
- `loadUserProfile()`: Loads user profile data
- `handleProfileImageUpload()`: Handles image upload
- `updateProfileImage()`: Updates profile on server

### Styling (`web/static/css/style.css`)

#### CSS Variables (web/static/css/style.css:1-25)
- Color scheme with primary, secondary, accent colors
- Typography and spacing variables
- Shadow and border radius definitions
- Responsive breakpoint considerations

#### Layout Components (web/static/css/style.css:27-150)
- App container with flex layout
- Sidebar with gradient header
- Main content area with rounded corners
- Responsive design patterns

#### UI Elements (web/static/css/style.css:152-400)
- User profile with avatar and edit overlay
- Subject and class selection buttons
- Progress bars with animations
- Message bubbles with different styles
- Input form with modern styling

#### Animations and Interactions (web/static/css/style.css:402-500)
- Message slide-in animations
- Typing indicator with bouncing dots
- Hover effects and transitions
- Focus states for accessibility
- Loading states and pulse animations

#### Responsive Design (web/static/css/style.css:502-600)
- Mobile-first approach
- Tablet and desktop breakpoints
- Collapsible sidebar for mobile
- Optimized typography scaling

## Testing

### Tool Integration Tests (`tests/test_tools.py`)

#### Test Suite (tests/test_tools.py:15-120)
- `test_imports()`: Verifies all module imports
- `test_database_connection()`: Tests PostgreSQL connectivity
- `test_context_class()`: Tests LearningContext with database
- `test_tools()`: Tests all learning tools with database integration

#### Features:
- Comprehensive error handling
- Database session management
- Progress tracking validation
- Tool invocation testing

### WebSocket Tests (`tests/test_websocket.py`)

#### Connection Testing (tests/test_websocket.py:25-60)
- WebSocket connection establishment
- Message sending and receiving
- Timeout handling (30 seconds)
- Error handling and logging

#### Command Line Interface:
- Configurable URL and message parameters
- Detailed logging output
- Success/failure status codes

## Dependencies

### Core Dependencies (`requirements.txt`)

#### Web Framework:
- `flask==3.0.0`: Web framework
- `flask-socketio==5.3.6`: WebSocket support
- `eventlet==0.33.3`: WSGI server

#### AI/ML:
- `langgraph>=0.2.40`: Agent orchestration
- `langchain-core>=0.3.17`: LangChain core functionality
- `langchain-community>=0.3.7`: Community tools
- `langchain-litellm>=0.2.0`: LiteLLM integration
- `litellm>=1.51.0`: LLM API gateway
- `typing-extensions>=4.12.2`: Type hints

#### Database:
- `sqlalchemy==2.0.35`: ORM
- `psycopg2-binary==2.9.10`: PostgreSQL driver
- `alembic==1.13.3`: Database migrations

#### Authentication:
- `passlib[bcrypt]==1.7.4`: Password hashing

#### Utilities:
- `python-dotenv==1.0.0`: Environment variables
- `pypdf==3.17.4`: PDF processing
- `colorlog==6.8.0`: Colored logging

## Environment Configuration

### Required Environment Variables

#### Database Connection:
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=learning_agent
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
```

#### AI/LLM Configuration:
```bash
LITELLM_URL=http://localhost:4000/
LITELLM_API_KEY=anything
MODEL_NAME=claude-4
```

#### Application Configuration:
```bash
FLASK_SECRET_KEY=learning-agent-secret-key
```

### Environment Files:
- `.env`: Production environment variables
- `.env.example`: Template for environment setup

## Key Features

### 1. AI-Powered Learning
- LangGraph-based agent architecture
- Integration with LiteLLM for model access
- Context-aware conversations
- Tool-enabled agent capabilities

### 2. Real-time Communication
- WebSocket-based chat interface
- Real-time message delivery
- Typing indicators
- Connection status monitoring

### 3. Progress Tracking
- Database-backed progress storage
- Chapter and section-level tracking
- Completion percentage calculation
- Visual progress indicators

### 4. User Management
- Secure authentication system
- Profile management with image upload
- Session-based authentication
- Password strength validation

### 5. Content Management
- PostgreSQL database for course content
- Hierarchical course structure
- Section-based content organization
- PDF processing capabilities

### 6. Modern Web Interface
- Responsive design for all devices
- Real-time updates without page refresh
- Intuitive user experience
- Professional styling and animations

## Architecture Patterns

### 1. Layered Architecture
- **Presentation Layer**: Web interface (HTML/CSS/JS)
- **Application Layer**: Flask API and WebSocket handlers
- **Business Logic Layer**: Agent system and tools
- **Data Access Layer**: SQLAlchemy models and database
- **Infrastructure Layer**: PostgreSQL database and external services

### 2. Agent Pattern
- LangGraph-based agent orchestration
- Tool-enabled agent capabilities
- State management for conversations
- Context-aware processing

### 3. Repository Pattern
- SQLAlchemy ORM for database abstraction
- Separation of data access logic
- Model-based entity representation
- Database migration management

### 4. Event-Driven Architecture
- WebSocket events for real-time communication
- Asynchronous message processing
- Event handling for user interactions
- State synchronization across components

### 5. Microservices Integration
- LiteLLM service for AI model access
- PostgreSQL as separate database service
- Modular tool system
- Configurable service endpoints

## File References Summary

### Core Application Files:
- `main.py`: CLI interface and agent runner
- `src/apis/app.py`: Main web application
- `requirements.txt`: Python dependencies
- `README.md`: Project documentation

### Database Files:
- `src/db/database.py`: Database configuration
- `src/models/models.py`: SQLAlchemy models
- `migrations/versions/001_initial_migration_create_all_tables.py`: Database schema

### Agent Files:
- `src/agents/ContextClass.py`: Learning context management
- `src/agents/AgentFactory.py`: Agent creation and execution

### Tool Files:
- `src/tools/ToolFactory.py`: Tool definitions and implementations

### Utility Files:
- `src/utils/auth.py`: Authentication utilities

### Web Interface Files:
- `web/templates/index.html`: Main chat interface
- `web/templates/auth.html`: Authentication interface
- `web/static/js/script.js`: Client-side JavaScript
- `web/static/css/style.css`: Application styling

### Test Files:
- `tests/test_tools.py`: Tool integration tests
- `tests/test_websocket.py`: WebSocket connection tests

This comprehensive reference provides a complete overview of the Learning Agent codebase, including all major components, their relationships, and detailed file-level documentation.