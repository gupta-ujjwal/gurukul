# Learning Agent Project Documentation

## Project Overview

The Learning Agent is a sophisticated AI-powered educational platform designed to provide personalized tutoring for CBSE Class 11 Physics students. Built with a modern web interface and powered by LangGraph agents, it offers interactive learning sessions, progress tracking, and a comprehensive chat-based learning experience.

## Current State Analysis

### Architecture & Technology Stack

**Backend Framework:**
- **Flask 3.0.0** - Core web framework with WebSocket support
- **Flask-SocketIO 5.3.6** - Real-time bidirectional communication
- **SQLite** - Database for user management and progress tracking
- **Eventlet** - Async worker for WebSocket handling

**AI & Agent Framework:**
- **LangGraph** - Agent orchestration and workflow management
- **LangChain Core** - Message handling and tool integration
- **LiteLLM** - LLM abstraction layer supporting multiple models
- **OpenAI Integration** - Primary LLM provider

**Frontend:**
- **Modern HTML5/CSS3/JavaScript** - Responsive web interface
- **Socket.IO Client** - Real-time communication
- **Font Awesome** - Icon library
- **Inter Font** - Modern typography

**Utilities:**
- **python-dotenv** - Environment management
- **pypdf** - PDF content extraction for learning materials
- **colorlog** - Enhanced logging

### Core Components

#### 1. Agent System (`AgentFactory.py`)
- **LangGraph-based agent architecture** with state management
- **Tool integration** for course content, progress tracking, and section retrieval
- **Context-aware conversations** with message history
- **Async processing** for responsive user experience
- **System instructions** enforcing CBSE Physics curriculum constraints

**Key Features:**
- Enforces use of only local NCERT content
- HTML-formatted responses (no markdown)
- 5-part teaching flow: recall, teach, practice, check, reflect
- MCQ generation and scoring capabilities
- Progress tracking and recommendations

#### 2. Context Management (`ContextClass.py`)
- **LearningContext class** for session state management
- **LangGraph State integration** with typed message handling
- **Progress tracking** across chapters and sections
- **Message history** conversion between formats
- **User session management** with timestamps

#### 3. Tool System (`ToolFactory.py`)
- **Four core learning tools:**
  - `get_course()` - Course structure and chapter mapping
  - `get_section_context()` - Content retrieval from PDF materials
  - `view_progress()` - Progress summary display
  - `update_progress()` - Score recording and advancement
- **PDF extraction capabilities** using pypdf
- **Global context management** for tool state
- **Error handling** for missing content

#### 4. Web Application (`app.py`)
- **Flask-SocketIO integration** for real-time chat
- **User authentication system** with signup/login
- **Profile management** with image upload
- **Progress tracking API** endpoints
- **Session management** with security middleware
- **Markdown to HTML conversion** for clean output

**Authentication Features:**
- Secure password hashing (SHA-256)
- Session-based authentication
- Profile image management
- User data persistence

#### 5. Frontend Interface

**Main Chat Interface (`templates/index.html`):**
- **Modern sidebar design** with user profile, subject selection, and progress tracking
- **Real-time chat** with typing indicators and message timestamps
- **Responsive design** with mobile optimization
- **Suggested questions** for guided learning
- **Progress visualization** with animated progress bars

**Authentication Page (`templates/auth.html`):**
- **Split-screen design** with feature highlights
- **Tab-based login/signup** forms
- **Form validation** and error handling
- **Responsive layout** for all devices

**Styling (`static/css/style.css`):**
- **Modern CSS variables** for consistent theming
- **Gradient backgrounds** and smooth animations
- **Responsive grid layouts** for subjects and suggestions
- **Custom scrollbar styling** and focus states
- **Mobile-first responsive design**

**JavaScript Functionality (`static/js/script.js`):**
- **Socket.IO integration** with connection management
- **Message formatting** with HTML conversion
- **Progress tracking** with API integration
- **Profile image upload** with validation
- **Keyboard shortcuts** and accessibility features

### Database Schema

**Student Table:**
- `id` (Primary Key)
- `name` - Student full name
- `class` - Grade level (9-12)
- `username` - Unique login identifier
- `password` - Hashed password
- `profile_image` - Base64 encoded avatar
- `created_at`, `updated_at` - Timestamps

**Progress_tracker Table:**
- `studentId` (Foreign Key)
- `subject` - Currently "Physics"
- `overall_progress` - Percentage completion
- `last_chapter_covered` - Last completed chapter
- `next_chapter` - Recommended next chapter
- `last_login_at` - Last activity timestamp

### Learning Materials

**Content Structure:**
- **PDF-based learning materials** stored in `LerningMaterial/Class 11/Physics/`
- **NCERT curriculum alignment** with CBSE Class 11 Physics
- **Current materials:**
  - `keph101.pdf` - Chapter 1: Units and Measurements
  - `keph102.pdf` - Chapter 2: Motion in a Straight Line

**Content Access:**
- **Dynamic PDF extraction** using pypdf library
- **Page-by-page text retrieval** with whitespace normalization
- **Error handling** for missing or corrupted files
- **Fallback mechanisms** when content unavailable

### Environment Configuration

**Required Environment Variables:**
```env
LITELLM_URL=https://grid.ai.juspay.net/
LITELLM_API_KEY=sk-CSnSGjczXsR85pOLJFpDkw
LITELLM_MODEL=gemini-2.5-pro
FLASK_ENV=development
FLASK_DEBUG=1
```

**Configuration Notes:**
- **LiteLLM integration** for model abstraction
- **Development mode** enabled for debugging
- **API key management** through environment variables

## Current Capabilities

### 1. Interactive Learning Sessions
- **Real-time chat interface** with instant responses
- **Context-aware conversations** maintaining session history
- **HTML-formatted educational content** with proper structure
- **Typing indicators** and connection status feedback

### 2. Curriculum Coverage
- **CBSE Class 11 Physics** focus (currently)
- **Structured course mapping** with chapters and sections
- **NCERT-aligned content** from official materials
- **Progressive learning** with topic sequencing

### 3. Progress Tracking
- **Visual progress indicators** with percentage completion
- **Topic coverage tracking** (20 topics total)
- **Session history** and learning analytics
- **Achievement recognition** and recommendations

### 4. User Management
- **Secure authentication** system
- **Profile customization** with avatar upload
- **Session persistence** across browser sessions
- **User data privacy** and security

### 5. Technical Features
- **WebSocket communication** for real-time updates
- **Responsive design** for all device sizes
- **Error handling** and recovery mechanisms
- **Logging and monitoring** for debugging

## Current Limitations

### 1. Subject Coverage
- **Physics-only** support currently implemented
- **Other subjects** (Chemistry, Math, Biology) disabled in UI
- **Class 11 focus** with other grades not yet supported

### 2. Content Limitations
- **Limited PDF materials** (only 2 chapters currently)
- **Static course mapping** without dynamic updates
- **No multimedia content** integration
- **Limited assessment types** (MCQs only)

### 3. Technical Constraints
- **Single-instance deployment** without scaling
- **File-based PDF storage** without content management
- **Basic authentication** without social login options
- **No offline capabilities** for content access

### 4. User Experience
- **No mobile app** (web-only interface)
- **Limited accessibility** features
- **No collaborative learning** capabilities
- **Basic progress analytics** without detailed insights

## Development Status

### Completed Features ✅
- Core LangGraph agent implementation
- Real-time chat interface with Socket.IO
- User authentication and profile management
- Progress tracking and visualization
- PDF content extraction system
- Responsive web design
- Basic error handling and logging

### In Progress 🔄
- Expansion of learning materials beyond 2 chapters
- Enhanced assessment capabilities
- Performance optimization for large user loads
- Improved content management system

### Planned Features 📋
- Multi-subject support (Chemistry, Math, Biology)
- Multi-class coverage (Grades 9-12)
- Advanced assessment types (essays, problems)
- Collaborative learning features
- Mobile application development
- Enhanced analytics and reporting
- Content recommendation engine
- Offline content access

## Technical Debt & Improvements Needed

### 1. Code Quality
- **Error handling** could be more comprehensive
- **Code documentation** needs improvement
- **Type hints** could be added throughout
- **Unit test coverage** is minimal

### 2. Performance
- **Database queries** could be optimized
- **PDF processing** could be cached
- **Frontend assets** could be minified
- **WebSocket connections** could be pooled

### 3. Security
- **Input validation** needs enhancement
- **Session management** could be more robust
- **API rate limiting** should be implemented
- **Content security policies** should be added

### 4. Scalability
- **Database schema** could be normalized
- **File storage** should use cloud services
- **Agent processing** could be distributed
- **Caching layer** should be implemented

## Deployment & Operations

### Current Setup
- **Single Flask application** with embedded Socket.IO
- **SQLite database** for simplicity
- **File-based content storage**
- **Environment-based configuration**

### Production Considerations
- **Database migration** to PostgreSQL/MySQL
- **Redis integration** for session management
- **Load balancing** for multiple instances
- **Container orchestration** with Docker/Kubernetes
- **Monitoring and alerting** systems
- **Backup and recovery** procedures

## Conclusion

The Learning Agent project represents a well-architected educational platform with a solid foundation for AI-powered tutoring. The current implementation successfully delivers an interactive learning experience for CBSE Class 11 Physics with modern web technologies and sophisticated agent orchestration.

Key strengths include the LangGraph-based agent system, real-time communication capabilities, and comprehensive user management. The project demonstrates good separation of concerns, modern frontend design, and practical integration of AI technologies.

The primary areas for expansion include broadening subject coverage, enhancing content management, improving scalability, and adding advanced learning features. With the current architecture in place, the project is well-positioned for incremental development and deployment in educational environments.

The codebase shows professional development practices with proper error handling, responsive design, and security considerations. While there are opportunities for optimization and expansion, the current state provides a functional and engaging learning platform that effectively demonstrates the potential of AI in education.