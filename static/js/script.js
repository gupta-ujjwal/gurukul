document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatMessages = document.getElementById('chat-messages');
    const messageForm = document.getElementById('message-form');
    const userInput = document.getElementById('user-input');
    const subjectButtons = document.querySelectorAll('.subject-btn');
    const classButtons = document.querySelectorAll('.class-btn');
    const topicPills = document.querySelectorAll('.topic-pill');
    
    // Initialize UI interactions
    initializeUIInteractions();
    
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
        // Map 'agent' role to 'assistant' for consistent styling
        const role = data.role === 'agent' ? 'assistant' : data.role;
        addMessage(role, data.content);
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
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        
        if (role === 'user') {
            messageDiv.classList.add('user-message');
            messageDiv.innerHTML = `<i class="fas fa-user-circle" style="margin-right: 8px; color: #4cc9f0;"></i> ${content}`;
        } else if (role === 'assistant' || role === 'agent') {
            messageDiv.classList.add('agent-message');
            messageDiv.innerHTML = `<i class="fas fa-robot" style="margin-right: 8px; color: #4361ee;"></i> ${formatAgentMessage(content)}`;
        } else {
            messageDiv.classList.add('system-message');
            messageDiv.innerHTML = `<i class="fas fa-info-circle" style="margin-right: 8px;"></i> ${content}`;
        }
        
        // Add timestamp
        const timeSpan = document.createElement('div');
        timeSpan.classList.add('message-time');
        const now = new Date();
        timeSpan.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        messageDiv.appendChild(timeSpan);
        
        chatMessages.appendChild(messageDiv);
        
        // Animate the message appearance
        setTimeout(() => {
            messageDiv.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 10);
    }
    
    // Function to add a system message
    function addSystemMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'system-message');
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        messageDiv.innerHTML = `<i class="fas fa-exclamation-triangle" style="margin-right: 8px;"></i> ${content}`;
        
        // Add timestamp
        const timeSpan = document.createElement('div');
        timeSpan.classList.add('message-time');
        const now = new Date();
        timeSpan.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        messageDiv.appendChild(timeSpan);
        
        chatMessages.appendChild(messageDiv);
        
        // Animate the message appearance
        setTimeout(() => {
            messageDiv.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 10);
        
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
    
    // Function to scroll to bottom of chat with smooth animation
    function scrollToBottom() {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    // Function to format agent messages
    function formatAgentMessage(content) {
        // Process emojis to make them more visible
        let formatted = content.replace(/([\u{1F300}-\u{1F6FF}])/gu, '<span class="emoji">$1</span>');
        
        // Convert markdown-style formatting to HTML if it still appears
        
        // Convert markdown-style bold to HTML
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Convert markdown-style headers to HTML
        formatted = formatted.replace(/##\s+([^\n]+)/g, '<h2>$1</h2>');
        formatted = formatted.replace(/###\s+([^\n]+)/g, '<h3>$1</h3>');
        formatted = formatted.replace(/#\s+([^\n]+)/g, '<h1>$1</h1>');
        
        // Convert markdown-style italic to HTML
        formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Convert markdown-style unordered lists
        formatted = formatted.replace(/^\s*-\s+(.+)$/gm, '<li>$1</li>');
        
        // Convert markdown-style ordered lists
        formatted = formatted.replace(/^\s*\d+\.\s+(.+)$/gm, '<li>$1</li>');
        
        // Wrap adjacent list items in ul/ol tags (simplified approach)
        formatted = formatted.replace(/(<li>.*<\/li>)(?!\n<li>)/gs, '<ul>$1</ul>');
        
        // Clean up any double-escaped HTML entities
        formatted = formatted.replace(/&amp;lt;/g, '&lt;');
        formatted = formatted.replace(/&amp;gt;/g, '&gt;');
        
        // Return the content with markdown converted to HTML
        return formatted;
    }
    
    // Helper function to escape HTML - not used anymore since content is already in HTML format
    function escapeHtml(text) {
        // Keeping this function for potential future use
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
    
    // Add a welcome animation
    setTimeout(() => {
        addMessage('assistant', 'Welcome to the Learning Agent! Type "let\'s start" to begin your physics learning journey. I\'m here to help you understand physics concepts in a fun and interactive way!');
    }, 500);
    
    // Function to initialize UI interactions
    function initializeUIInteractions() {
        // Subject button click handlers
        subjectButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all subject buttons
                subjectButtons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                this.classList.add('active');
                
                // Update header text based on selected subject
                const subjectName = this.textContent;
                const headerSubtitle = document.querySelector('header p');
                const activeClass = document.querySelector('.class-btn.active').textContent;
                headerSubtitle.textContent = `Your CBSE Class ${activeClass} ${subjectName} Tutor`;
                
                // Add a system message about subject change
                addSystemMessage(`Switched to ${subjectName} for Class ${activeClass}`);
            });
        });
        
        // Class button click handlers
        classButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all class buttons
                classButtons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                this.classList.add('active');
                
                // Update header text based on selected class
                const className = this.textContent;
                const headerSubtitle = document.querySelector('header p');
                const activeSubject = document.querySelector('.subject-btn.active').textContent;
                headerSubtitle.textContent = `Your CBSE Class ${className} ${activeSubject} Tutor`;
                
                // Add a system message about class change
                addSystemMessage(`Switched to Class ${className} for ${activeSubject}`);
            });
        });
        
        // Topic pill click handlers
        topicPills.forEach(pill => {
            pill.addEventListener('click', function() {
                const topicName = this.textContent;
                userInput.value = `Tell me about ${topicName}`;
                userInput.focus();
            });
        });
    }
});
