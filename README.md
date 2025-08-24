# Learning Agent Web Interface

A web-based chat interface for the CBSE Class 11 Physics Learning Agent.

## Features

- Real-time chat interface using WebSockets
- Clean, responsive design
- Comprehensive Markdown formatting support:
  - Headers (h1, h2, h3)
  - Bold and italic text
  - Code blocks with language-specific styling
  - Inline code
  - Ordered and unordered lists
  - Blockquotes
  - Horizontal rules
  - Links
  - Tables
- Typing indicators
- Message timestamps
- Error handling and connection status indicators
- Automatic reconnection on disconnection

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- The JAF framework and its dependencies

## Installation

1. Clone this repository or download the files.

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Make sure you have the JAF framework and LiteLLM set up correctly.

## Running the Application

### Using the Provided Scripts

#### On Unix/Linux/Mac:

```bash
# Make the script executable (if needed)
chmod +x run.sh

# Run the application
./run.sh
```

#### On Windows:

```
run.bat
```

### Manual Start

If you prefer to start the application manually:

```bash
python app.py
```

Once started, open your browser and navigate to:

```
http://localhost:5000
```

Start chatting with the Learning Agent by typing "let's start" or any other message.

## Troubleshooting

If you encounter issues with the chat interface:

1. **Messages not being processed**:
   - Check the server logs for errors
   - Ensure LiteLLM is running and accessible
   - Verify that the JAF framework is properly installed

2. **Connection issues**:
   - Make sure the server is running
   - Check for any firewall blocking WebSocket connections
   - Try using a different browser

3. **Slow responses**:
   - The agent processing might take time depending on the complexity of the query
   - Check server resources (CPU/memory usage)

4. **Server crashes**:
   - Check the logs for error messages
   - Ensure all dependencies are correctly installed
   - Verify that the environment variables are set correctly

## Project Structure

```
learning-agent/
├── app.py                 # Flask application with WebSocket support
├── main.py                # Original CLI application
├── AgentFactory.py        # Agent creation logic
├── ContextClass.py        # Context management
├── ToolFactory.py         # Agent tools
├── requirements.txt       # Project dependencies
├── static/                # Static assets
│   ├── css/
│   │   └── style.css      # Styling for the web interface
│   └── js/
│       └── script.js      # Client-side JavaScript
└── templates/
    └── index.html         # HTML template for the web interface
```

## Environment Variables

The application uses the following environment variables:

- `LITELLM_URL`: URL for the LiteLLM service (default: "http://localhost:4000/")
- `LITELLM_API_KEY`: API key for LiteLLM (default: "anything")

You can set these in a `.env` file in the project root.

## Customization

- Modify `static/css/style.css` to change the appearance
- Update `templates/index.html` to change the layout
- Edit `static/js/script.js` to modify client-side behavior

## Markdown Formatting

The chat interface supports comprehensive Markdown formatting for agent messages. To see examples and test the formatting:

1. Start the server and navigate to `http://localhost:5000`
2. Or open `static/markdown_test.html` directly in your browser to see examples and test different markdown syntax

The markdown test page provides:
- Examples of all supported markdown elements
- Side-by-side comparison of markdown syntax and rendered output
- A live editor to test your own markdown formatting

## License

[Your License Here]
