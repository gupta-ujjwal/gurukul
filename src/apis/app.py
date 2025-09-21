import asyncio
import os
import json
import logging
import sys
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit

# Add the project root to Python path to enable imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.agents.ContextClass import LearningContext
from src.agents.AgentFactory import create_learning_agent, run_learning_agent_async
from src.db.database import SessionLocal, engine, Base
from src.models.models import *
from src.utils.auth import get_password_hash, verify_password, is_password_strong
from src.routes.admin import admin_bp

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
# Use absolute paths for static and template folders
basedir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.dirname(os.path.dirname(basedir))  # Go up two levels from src/apis to project root
static_folder = os.path.join(project_root, 'web', 'static')
template_folder = os.path.join(project_root, 'web', 'templates')

app = Flask(__name__, static_folder=static_folder, template_folder=template_folder)
app.config['SECRET_KEY'] = 'learning-agent-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Register admin blueprint
app.register_blueprint(admin_bp)

# Learning context will be created dynamically per user session
context = None

# Initialize the LangGraph agent
agent_graph = None

def initialize_agent():
    """Initialize the LangGraph agent."""
    global agent_graph
    try:
        agent_graph = create_learning_agent()
        logger.info("✓ LangGraph agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {str(e)}")
        raise

def get_user_context():
    """Get or create learning context for the current user."""
    global context
    
    # If user is authenticated, create context with their data
    if 'student_id' in session:
        student_id = session['student_id']
        db = get_db()
        try:
            student = db.query(Student).filter(Student.id == student_id).first()
            if student:
                context = LearningContext(
                    user_id=student.username,
                    session_id=session.get('session_id', f"session_{student_id}"),
                    progress={},
                    past_messages=[],
                )
                return context
        finally:
            db.close()
    
    # If no authenticated user, return None or create a temporary context
    return None

# Database helper functions
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# Initialize database tables
def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created successfully")

# Authentication middleware
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/auth')
def auth():
    if 'student_id' in session:
        return redirect(url_for('index'))
    return render_template('auth.html')

@app.route('/signup', methods=['POST'])
def signup():
    """Handle user registration."""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        class_name = data.get('class', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not all([name, class_name, username, password]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Validate class is a number
        try:
            class_grade = int(class_name)
            if not (9 <= class_grade <= 12):
                return jsonify({'success': False, 'message': 'Class must be between 9 and 12'})
        except ValueError:
            return jsonify({'success': False, 'message': 'Class must be a valid number'})
        
        # Check password strength
        is_strong, strength_msg = is_password_strong(password)
        if not is_strong:
            return jsonify({'success': False, 'message': strength_msg})
        
        db = get_db()
        try:
            # Check if username already exists
            existing_student = db.query(Student).filter(Student.username == username).first()
            if existing_student:
                return jsonify({'success': False, 'message': 'Username already exists'})
            
            # Create new student without default profile image
            new_student = Student(
                full_name=name,
                class_grade=class_grade,
                username=username,
                hashed_password=get_password_hash(password),
                profile_image=None  # No default avatar
            )
            
            db.add(new_student)
            db.commit()
            db.refresh(new_student)
            
            return jsonify({
                'success': True, 
                'message': 'Account created successfully',
                'student_id': new_student.id
            })
            
        except Exception as e:
            db.rollback()
            logger.error(f"Signup error: {str(e)}")
            return jsonify({'success': False, 'message': 'An error occurred during signup'})
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Signup request error: {str(e)}")
        return jsonify({'success': False, 'message': 'Invalid request data'})

@app.route('/login', methods=['POST'])
def login():
    """Handle user login."""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not all([username, password]):
            return jsonify({'success': False, 'message': 'Username and password are required'})
        
        db = get_db()
        try:
            # Find student by username
            student = db.query(Student).filter(Student.username == username).first()
            
            if not student:
                return jsonify({'success': False, 'message': 'Invalid username or password'})
            
            # Verify password
            if not verify_password(password, student.hashed_password):
                return jsonify({'success': False, 'message': 'Invalid username or password'})
            
            # Update last login timestamp
            student.updated_at = datetime.now()
            db.commit()
            
            # Set session
            session['student_id'] = student.id
            session['username'] = student.username
            session['full_name'] = student.full_name
            session['class_grade'] = student.class_grade
            
            return jsonify({
                'success': True, 
                'message': 'Login successful',
                'student': {
                    'id': student.id,
                    'name': student.full_name,
                    'class': student.class_grade,
                    'username': student.username
                }
            })
            
        except Exception as e:
            db.rollback()
            logger.error(f"Login error: {str(e)}")
            return jsonify({'success': False, 'message': 'An error occurred during login'})
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Login request error: {str(e)}")
        return jsonify({'success': False, 'message': 'Invalid request data'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/api/progress')
@login_required
def get_progress():
    """Get student progress data."""
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({'success': False, 'message': 'Not authenticated'})
        
        db = get_db()
        try:
            # Get all progress records for this student
            progress_records = db.query(Progress).filter(Progress.student_id == student_id).all()
            
            # Calculate overall progress
            if progress_records:
                total_completion = sum(record.completion_percent for record in progress_records)
                overall_progress = min(100.0, total_completion / len(progress_records))
                
                # Get the most recently accessed chapter/section
                latest_progress = max(progress_records, key=lambda x: x.last_accessed_at)
                last_chapter = f"Chapter {latest_progress.chapter.number}: {latest_progress.chapter.title}" if latest_progress.chapter else ''
                
                # Simple logic for next chapter (in a real app, this would be more sophisticated)
                next_chapter = "Continue with next section"
            else:
                overall_progress = 0.0
                last_chapter = ''
                next_chapter = 'Start with Chapter 1'
            
            # Calculate topics covered based on actual sections in database
            db = get_db()
            try:
                # Get total number of sections across all courses
                total_sections = db.query(Section).count()
                # Get number of sections with progress > 0 for this student
                completed_sections = db.query(Progress).filter(
                    Progress.student_id == student_id,
                    Progress.completion_percent > 0
                ).count()
                
                total_topics = total_sections if total_sections > 0 else 1
                topics_covered = completed_sections
            except Exception as e:
                logger.error(f"Error calculating topics: {str(e)}")
                total_topics = 1
                topics_covered = 0
            finally:
                db.close()
            
            return jsonify({
                'success': True,
                'data': {
                    'overall_progress': round(overall_progress, 2),
                    'topics_covered': topics_covered,
                    'total_topics': total_topics,
                    'last_chapter': last_chapter,
                    'next_chapter': next_chapter
                }
            })
            
        except Exception as e:
            logger.error(f"Progress fetch error: {str(e)}")
            return jsonify({'success': False, 'message': 'An error occurred while fetching progress'})
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Progress request error: {str(e)}")
        return jsonify({'success': False, 'message': 'Invalid request'})

@app.route('/api/progress', methods=['POST'])
@login_required
def update_progress():
    """Update student progress."""
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({'success': False, 'message': 'Not authenticated'})
        
        data = request.get_json()
        course_id = data.get('course_id')  # UUID string
        chapter_id = data.get('chapter_id')  # Integer
        section_id = data.get('section_id')  # Integer
        completion_percent = data.get('completion_percent', 0.0)
        
        # Validate input
        if not all([course_id, chapter_id, section_id]):
            return jsonify({'success': False, 'message': 'Course, chapter, and section IDs are required'})
        
        try:
            completion_percent = float(completion_percent)
            if not (0.0 <= completion_percent <= 100.0):
                return jsonify({'success': False, 'message': 'Completion percentage must be between 0 and 100'})
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid completion percentage'})
        
        db = get_db()
        try:
            # Check if the course, chapter, and section exist
            course = db.query(Course).filter(Course.id == course_id).first()
            chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
            section = db.query(Section).filter(Section.id == section_id).first()
            
            if not all([course, chapter, section]):
                return jsonify({'success': False, 'message': 'Invalid course, chapter, or section'})
            
            # Check if progress record already exists
            existing_progress = db.query(Progress).filter(
                Progress.student_id == student_id,
                Progress.course_id == course_id,
                Progress.chapter_id == chapter_id,
                Progress.section_id == section_id
            ).first()
            
            if existing_progress:
                # Update existing progress
                existing_progress.completion_percent = completion_percent
                existing_progress.last_accessed_at = datetime.now()
            else:
                # Create new progress record
                new_progress = Progress(
                    student_id=student_id,
                    course_id=course_id,
                    chapter_id=chapter_id,
                    section_id=section_id,
                    completion_percent=completion_percent
                )
                db.add(new_progress)
            
            db.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Progress updated successfully',
                'completion_percent': completion_percent
            })
            
        except Exception as e:
            db.rollback()
            logger.error(f"Progress update error: {str(e)}")
            return jsonify({'success': False, 'message': 'An error occurred while updating progress'})
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Progress update request error: {str(e)}")
        return jsonify({'success': False, 'message': 'Invalid request data'})

@app.route('/api/profile')
@login_required
def get_profile():
    """Get student profile data."""
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({'success': False, 'message': 'Not authenticated'})
        
        db = get_db()
        try:
            # Get student profile data
            student = db.query(Student).filter(Student.id == student_id).first()
            
            if not student:
                return jsonify({'success': False, 'message': 'Student not found'})
            
            # No default avatar - require user to upload one
            
            if not student.profile_image:
                return jsonify({'success': False, 'message': 'No profile image found. Please upload a profile image.'})
            
            profile_image = student.profile_image
            
            return jsonify({
                'success': True,
                'data': {
                    'id': student.id,
                    'name': student.full_name,
                    'class': student.class_grade,
                    'username': student.username,
                    'profile_image': profile_image,
                    'created_at': student.created_at.isoformat() if student.created_at else None,
                    'updated_at': student.updated_at.isoformat() if student.updated_at else None
                }
            })
            
        except Exception as e:
            logger.error(f"Profile fetch error: {str(e)}")
            return jsonify({'success': False, 'message': 'An error occurred while fetching profile'})
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Profile request error: {str(e)}")
        return jsonify({'success': False, 'message': 'Invalid request'})

@app.route('/api/profile/image', methods=['POST'])
@login_required
def update_profile_image():
    """Update student profile image."""
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({'success': False, 'message': 'Not authenticated'})
        
        data = request.get_json()
        profile_image = data.get('profile_image', '')
        
        if not profile_image:
            return jsonify({'success': False, 'message': 'No image provided'})
        
        # Validate that it's a valid base64 image
        if not profile_image.startswith('data:image/'):
            return jsonify({'success': False, 'message': 'Invalid image format'})
        
        # Basic size validation (check if base64 data is reasonable size)
        if len(profile_image) > 1000000:  # 1MB limit
            return jsonify({'success': False, 'message': 'Image size too large'})
        
        db = get_db()
        try:
            # Get student and update profile image
            student = db.query(Student).filter(Student.id == student_id).first()
            
            if not student:
                return jsonify({'success': False, 'message': 'Student not found'})
            
            student.profile_image = profile_image
            student.updated_at = datetime.now()
            db.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Profile image updated successfully',
                'profile_image': profile_image
            })
            
        except Exception as e:
            db.rollback()
            logger.error(f"Profile image update error: {str(e)}")
            return jsonify({'success': False, 'message': 'An error occurred while updating profile image'})
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Profile image update request error: {str(e)}")
        return jsonify({'success': False, 'message': 'Invalid request data'})

# Socket events
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('message', {'role': 'agent', 'content': '📝 Hi this is your personal Learning Agent - Type a message to begin!'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('message')
def handle_message(data):
    user_input = data.get('message', '').strip()
    
    logger.info(f"Received message: {user_input}")
    
    if not user_input:
        logger.warning("Empty message received, ignoring")
        return
    
    # Get user context in the request context (where session is available)
    user_context = get_user_context()
    if user_context is None:
        socketio.emit('message', {'role': 'assistant', 'content': "Please log in to use the learning agent."})
        return
    
    # Create a background task to process the message with context
    logger.info("Starting background task to process message")
    socketio.start_background_task(target=run_async_message, user_input=user_input, user_context=user_context)

def run_async_message(user_input, user_context):
    """Wrapper function to run the async process_message function in a background task."""
    logger.info("Setting up async loop for message processing")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        logger.info("Running process_message in the loop")
        loop.run_until_complete(process_message(user_input, user_context))
    except Exception as e:
        logger.error(f"Error in run_async_message: {str(e)}")
        socketio.emit('message', {'role': 'agent', 'content': f"An error occurred while processing your message: {str(e)}"})
    finally:
        logger.info("Closing async loop")
        loop.close()

async def process_message(user_input, user_context):
    global agent_graph
    
    logger.info("Processing message with LangGraph agent")
    
    try:
        if agent_graph is None:
            logger.error("Agent not initialized")
            socketio.emit('message', {'role': 'assistant', 'content': "Error: Agent not initialized. Please refresh the page."})
            return
        
        logger.info("Running LangGraph agent with the message")
        response = await run_learning_agent_async(agent_graph, user_input, user_context)
        
        logger.info("Message processed successfully")
        
        # Post-process the output to ensure proper HTML formatting
        output = response
        
        # Convert markdown-style formatting to HTML if needed
        output = convert_markdown_to_html(output)
        
        logger.info("Post-processed markdown to HTML")
        
        socketio.emit('message', {'role': 'assistant', 'content': output})
        
    except Exception as e:
        logger.error(f"Exception in process_message: {str(e)}", exc_info=True)
        socketio.emit('message', {'role': 'assistant', 'content': f"An error occurred: {str(e)}"})

def convert_markdown_to_html(markdown_text: str) -> str:
    """
    Convert Markdown text to clean, formatted plain text.
    """

    text = markdown_text

    # Convert headings (e.g., ## Heading → HEADING\n)
    text = re.sub(r'^(#+)\s*(.*)', lambda m: m.group(2).upper(), text, flags=re.MULTILINE)

    # Bold (**text** or __text__)
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)

    # Italics (*text* or _text_)
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)

    # Inline code (`code`)
    text = re.sub(r'`([^`]*)`', r'\1', text)

    # Code blocks (```...```)
    text = re.sub(r'```[\s\S]*?```', lambda m: m.group(0).replace("```", "").strip(), text)

    # Links: [text](url) → text (url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', text)

    # Images: ![alt](url) → alt (url)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'\1 (\2)', text)

    # Lists: keep bullets consistent
    text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', lambda m: f"{m.group(0).strip()} ", text, flags=re.MULTILINE)

    # Remove extra markdown characters (>, --- separators)
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n-{3,}\n', '\n', text)

    # Collapse multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

# Run the app
if __name__ == '__main__':
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("✓ Loaded environment variables from .env file")
    except ImportError:
        logger.warning("⚠️ python-dotenv not installed, using system env variables")
    
    # Initialize the database
    init_db()
    logger.info("✓ Database initialized")
    
    # Initialize the agent before starting the server
    initialize_agent()
    
    logger.info("Starting the Flask-SocketIO server with LangGraph")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)