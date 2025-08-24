document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatMessages = document.getElementById('chat-messages');
    const messageForm = document.getElementById('message-form');
    const userInput = document.getElementById('user-input');
    
    // Initialize Socket.io connection with error handling
    const socket = io({
        reconnectionAttempts: 5,
        timeout: 10000,
        reconnectionDelay: 1000
    });
    let isWaitingForResponse = false;
    let connectionTimeout;
    
    // Connect to WebSocket
    socket.on('connect', function() {
        console.log('Connected to server');
        clearTimeout(connectionTimeout);
        
        // Remove any connection error messages
        const connectionError = document.querySelector('.connection-error');
        if (connectionError) {
            connectionError.remove();
        }
    });
    
    // Set a connection timeout
    connectionTimeout = setTimeout(function() {
        if (!socket.connected) {
            console.error('Connection timeout');
            addSystemMessage('Connection timeout. Please check if the server is running and refresh the page.');
        }
    }, 5000);
    
    // Handle incoming messages
    socket.on('message', function(data) {
        removeTypingIndicator();
        isWaitingForResponse = false;
        addMessage(data.role, data.content);
        scrollToBottom();
    });
    
    // Handle disconnection
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        addSystemMessage('Disconnected from server. Please refresh the page.');
        isWaitingForResponse = false;
    });
    
    // Handle connection errors
    socket.on('connect_error', function(error) {
        console.error('Connection error:', error);
        addSystemMessage('Failed to connect to server. Please check if the server is running and refresh the page.');
        isWaitingForResponse = false;
    });
    
    // Handle reconnection attempts
    socket.on('reconnect_attempt', function(attemptNumber) {
        console.log(`Attempting to reconnect (${attemptNumber})`);
    });
    
    // Handle successful reconnection
    socket.on('reconnect', function(attemptNumber) {
        console.log(`Reconnected after ${attemptNumber} attempts`);
        addSystemMessage('Reconnected to server.');
    });
    
    // Handle reconnection errors
    socket.on('reconnect_error', function(error) {
        console.error('Reconnection error:', error);
    });
    
    // Handle reconnection failure
    socket.on('reconnect_failed', function() {
        console.error('Failed to reconnect');
        addSystemMessage('Failed to reconnect to server. Please refresh the page.');
    });
    
    // Handle errors
    socket.on('error', function(error) {
        console.error('Socket error:', error);
        addSystemMessage('An error occurred with the connection. Please refresh the page.');
        isWaitingForResponse = false;
    });
    
    // Handle form submission
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (message && !isWaitingForResponse) {
            // Clear input field
            userInput.value = '';
            
            // Add user message to chat
            addMessage('user', message);
            
            // Show typing indicator
            addTypingIndicator();
            
            try {
                // Send message to server
                socket.emit('message', { message: message }, function(acknowledgement) {
                    console.log('Message acknowledged:', acknowledgement);
                });
                
                // Set waiting flag
                isWaitingForResponse = true;
                
                // Set a timeout to reset the waiting flag in case of no response
                setTimeout(function() {
                    if (isWaitingForResponse) {
                        console.warn('No response received within timeout period');
                        removeTypingIndicator();
                        isWaitingForResponse = false;
                        addSystemMessage('No response received. Please try again.');
                    }
                }, 30000); // 30 seconds timeout
            } catch (error) {
                console.error('Error sending message:', error);
                removeTypingIndicator();
                addSystemMessage('Failed to send message. Please try again.');
            }
            
            // Scroll to bottom
            scrollToBottom();
        } else if (isWaitingForResponse) {
            // Inform user that we're still waiting for a response
            addSystemMessage('Please wait for the current response to complete.');
        }
    });
    
    // Function to add a message to the chat
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        
        if (role === 'user') {
            messageDiv.classList.add('user-message');
            messageDiv.textContent = content;
        } else if (role === 'agent') {
            messageDiv.classList.add('agent-message');
            messageDiv.innerHTML = formatAgentMessage(content);
        } else {
            messageDiv.classList.add('system-message');
            messageDiv.textContent = content;
        }
        
        // Add timestamp
        const timeSpan = document.createElement('div');
        timeSpan.classList.add('message-time');
        const now = new Date();
        timeSpan.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        messageDiv.appendChild(timeSpan);
        
        chatMessages.appendChild(messageDiv);
    }
    
    // Function to add a system message
    function addSystemMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'system-message');
        messageDiv.textContent = content;
        
        // Add timestamp
        const timeSpan = document.createElement('div');
        timeSpan.classList.add('message-time');
        const now = new Date();
        timeSpan.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        messageDiv.appendChild(timeSpan);
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Function to add typing indicator
    function addTypingIndicator() {
        // Remove any existing typing indicators
        removeTypingIndicator();
        
        // Create typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('typing-indicator', 'message', 'agent-message');
        typingDiv.innerHTML = `
            <span></span>
            <span></span>
            <span></span>
        `;
        
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }
    
    // Function to remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Function to scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to format agent messages with Markdown syntax
    function formatAgentMessage(content) {
        // First, escape any HTML to prevent XSS
        let formatted = escapeHtml(content);
        
        // Process code blocks with language highlighting
        formatted = formatted.replace(/```(\w+)?\n([\s\S]+?)```/g, function(match, language, code) {
            return `<pre class="code-block${language ? ' language-'+language : ''}"><code>${code.trim()}</code></pre>`;
        });
        
        // Process inline code
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Process headers
        formatted = formatted.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
        formatted = formatted.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
        formatted = formatted.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
        
        // Process bold text
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Process italic text
        formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Process ordered lists
        formatted = formatted.replace(/^\d+\. (.+?)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/(<li>.*<\/li>)(?!\n<li>)/gs, '<ol>$1</ol>');
        
        // Process unordered lists
        formatted = formatted.replace(/^- (.+?)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/(<li>.*<\/li>)(?!\n<li>)/gs, '<ul>$1</ul>');
        
        // Process blockquotes
        formatted = formatted.replace(/^> (.+?)$/gm, '<blockquote>$1</blockquote>');
        
        // Process horizontal rules
        formatted = formatted.replace(/^---$/gm, '<hr>');
        
        // Process links
        formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        
        // Process tables (basic implementation)
        formatted = formatted.replace(/^\|(.+)\|$/gm, '<tr>$1</tr>');
        formatted = formatted.replace(/\|([^|]+)\|/g, '<td>$1</td>');
        formatted = formatted.replace(/<tr>(.+?)<\/tr>/g, function(match) {
            if (match.includes('---')) {
                return ''; // Remove separator row
            }
            return match;
        });
        formatted = formatted.replace(/(<tr>.*<\/tr>)(?!\n<tr>)/gs, '<table>$1</table>');
        
        // Process emojis to make them more visible
        formatted = formatted.replace(/([\u{1F300}-\u{1F6FF}])/gu, '<span class="emoji">$1</span>');
        
        // Reduce excessive line breaks
        formatted = formatted.replace(/<br><br><br>/g, '<br><br>');
        
        // Replace newlines with <br> for remaining text
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Add paragraph tags for better spacing
        formatted = formatted.replace(/(.+?)(?=<br>|$)/g, function(match) {
            // Skip if the match already has HTML tags
            if (match.match(/<[^>]+>/)) {
                return match;
            }
            return `<p>${match}</p>`;
        });
        
        // Clean up any empty paragraphs
        formatted = formatted.replace(/<p><\/p>/g, '');
        
        return formatted;
    }
    
    // Helper function to escape HTML
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
    
    // Focus input field on load
    userInput.focus();
});
