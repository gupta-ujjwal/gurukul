import asyncio
import os
import json
import logging
import sys
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from jaf import (
    run, make_litellm_provider,
    RunState, RunConfig, Message,
    generate_run_id, generate_trace_id, ModelConfig
)
from ContextClass import LearningContext
from AgentFactory import create_learning_agent

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
    session_id=generate_run_id(),
    user_id="user_123",  # In real scenarios, fetch from auth system
    progress={},
    past_messages=[],
)

# Initialize the agent and model provider
litellm_url = os.getenv("LITELLM_URL", "http://localhost:4000/")
litellm_api_key = os.getenv("LITELLM_API_KEY", "anything")
model_provider = make_litellm_provider(litellm_url, litellm_api_key)
learning_agent = create_learning_agent()

# Configure the agent run
config = RunConfig(
    agent_registry={"LearningAgent": learning_agent},
    model_provider=model_provider,
    max_turns=30,
)

# Turn counter
turn_count = 0

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
    global turn_count
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
    global turn_count, context
    
    logger.info("Creating RunState for message processing")
    old_messages = context.past_messages if context.past_messages else []
    user_messages = [Message(role="user", content=user_input)]
    state = RunState(
        run_id=generate_run_id(),
        trace_id=generate_trace_id(),
        messages=old_messages+user_messages,
        current_agent_name="LearningAgent",
        context=context,
        turn_count=turn_count,
    )
    
    try:
        logger.info("Running agent with the message")
        result = await run(state, config)
        turn_count += 1
        
        if result.outcome.status == "completed":
            logger.info("Message processed successfully")
            
            # Post-process the output to ensure proper HTML formatting
            output = result.outcome.output
            
            # Convert markdown-style formatting to HTML
            import re
            
            # Convert markdown-style bold to HTML
            output = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', output)
            
            # Convert markdown-style headers to HTML
            output = re.sub(r'###\s+([^\n]+)', r'<h3>\1</h3>', output)
            output = re.sub(r'##\s+([^\n]+)', r'<h2>\1</h2>', output)
            output = re.sub(r'#\s+([^\n]+)', r'<h1>\1</h1>', output)
            
            # Convert markdown-style italic to HTML
            output = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', output)
            
            # Convert markdown-style unordered lists
            output = re.sub(r'^\s*-\s+(.+)$', r'<li>\1</li>', output, flags=re.MULTILINE)
            
            # Convert markdown-style ordered lists
            output = re.sub(r'^\s*\d+\.\s+(.+)$', r'<li>\1</li>', output, flags=re.MULTILINE)
            
            # Wrap adjacent list items in ul tags (simplified approach)
            output = re.sub(r'(<li>.*?</li>)(?!\n<li>)', r'<ul>\1</ul>', output, flags=re.DOTALL)
            
            logger.info("Post-processed markdown to HTML")
            
            context.past_messages.append(Message(role="user", content=user_input))
            context.past_messages.append(Message(role="assistant", content=output))
            socketio.emit('message', {'role': 'assistant', 'content': output})
        else:
            logger.error(f"Error in agent processing: {result.outcome.error}")
            socketio.emit('message', {'role': 'assistant', 'content': f"Error: {result.outcome.error}"})
    except Exception as e:
        logger.error(f"Exception in process_message: {str(e)}", exc_info=True)
        socketio.emit('message', {'role': 'assistant', 'content': f"An error occurred: {str(e)}"})

# Helper function to run async code in the background
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# Run the app
if __name__ == '__main__':
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("✓ Loaded environment variables from .env file")
    except ImportError:
        logger.warning("⚠️ python-dotenv not installed, using system env variables")
    
    logger.info("Starting the Flask-SocketIO server")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
