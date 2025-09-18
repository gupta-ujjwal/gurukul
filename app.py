import asyncio
import os
import json
import logging
import sys
import re
import sqlite3
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from ContextClass import LearningContext
from AgentFactory import create_learning_agent, run_learning_agent_async

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
app = Flask(__name__)
app.config['SECRET_KEY'] = 'learning-agent-secret-key'
app.config['DATABASE'] = 'instance/learning_agent.db'
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Initialize the learning context
context = LearningContext(
    session_id="web_session_001",
    user_id="user_123",  # In real scenarios, fetch from auth system
    progress={},
    past_messages=[],
)

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

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
    try:
        data = request.get_json()
        name = data.get('name')
        class_name = data.get('class')
        username = data.get('username')
        password = data.get('password')
        
        if not all([name, class_name, username, password]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute('SELECT id FROM Student WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        # Create new student
        hashed_password = hash_password(password)
        cursor.execute('''
            INSERT INTO Student (name, class, username, password, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, class_name, username, hashed_password, datetime.now(), datetime.now()))
        
        student_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Account created successfully'})
        
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred during signup'})

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({'success': False, 'message': 'Username and password are required'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find student by username
        cursor.execute('SELECT id, password FROM Student WHERE username = ?', (username,))
        student = cursor.fetchone()
        
        if not student:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid username or password'})
        
        # Verify password
        hashed_password = hash_password(password)
        if student['password'] != hashed_password:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid username or password'})
        
        # Update last login
        cursor.execute('UPDATE Student SET updated_at = ? WHERE id = ?', (datetime.now(), student['id']))
        conn.commit()
        conn.close()
        
        # Set session
        session['student_id'] = student['id']
        session['username'] = username
        
        return jsonify({'success': True, 'message': 'Login successful'})
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred during login'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

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
    
    # Create a background task to process the message
    logger.info("Starting background task to process message")
    socketio.start_background_task(target=run_async_message, user_input=user_input)

def run_async_message(user_input):
    """Wrapper function to run the async process_message function in a background task."""
    logger.info("Setting up async loop for message processing")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        logger.info("Running process_message in the loop")
        loop.run_until_complete(process_message(user_input))
    except Exception as e:
        logger.error(f"Error in run_async_message: {str(e)}")
        socketio.emit('message', {'role': 'agent', 'content': f"An error occurred while processing your message: {str(e)}"})
    finally:
        logger.info("Closing async loop")
        loop.close()

async def process_message(user_input):
    global context, agent_graph
    
    logger.info("Processing message with LangGraph agent")
    
    try:
        if agent_graph is None:
            logger.error("Agent not initialized")
            socketio.emit('message', {'role': 'assistant', 'content': "Error: Agent not initialized. Please refresh the page."})
            return
            
        logger.info("Running LangGraph agent with the message")
        response = await run_learning_agent_async(agent_graph, user_input, context)
        
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
    
    # Initialize the agent before starting the server
    initialize_agent()
    
    logger.info("Starting the Flask-SocketIO server with LangGraph")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)