import asyncio
import os
import json
import logging
import sys
import re
from flask import Flask, render_template, request, jsonify
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

# Routes
@app.route('/')
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

def convert_markdown_to_html(text):
    """Convert markdown-style formatting to HTML."""
    if not text:
        return text
    
    # Convert markdown-style bold to HTML
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    
    # Convert markdown-style headers to HTML
    text = re.sub(r'###\s+([^\n]+)', r'<h3>\1</h3>', text)
    text = re.sub(r'##\s+([^\n]+)', r'<h2>\1</h2>', text)
    text = re.sub(r'#\s+([^\n]+)', r'<h1>\1</h1>', text)
    
    # Convert markdown-style italic to HTML
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    
    # Convert markdown-style unordered lists
    text = re.sub(r'^\s*-\s+(.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    
    # Convert markdown-style ordered lists
    text = re.sub(r'^\s*\d+\.\s+(.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    
    # Wrap adjacent list items in ul tags (simplified approach)
    text = re.sub(r'(<li>.*?</li>)(?!\n<li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
    
    # Convert line breaks to <br> tags for better HTML display
    text = re.sub(r'\n\n+', '<br><br>', text)
    text = re.sub(r'\n', '<br>', text)
    
    return text

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
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)