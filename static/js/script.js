document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatMessages = document.getElementById('chat-messages');
    const messageForm = document.getElementById('message-form');
    const userInput = document.getElementById('user-input');
    const subjectButtons = document.querySelectorAll('.subject-btn');
    const classButtons = document.querySelectorAll('.class-btn');
    const topicPills = document.querySelectorAll('.topic-pill');
    const suggestionButtons = document.querySelectorAll('.suggestion-btn');
    const toggleSidebarBtn = document.getElementById('toggle-sidebar');
    const clearChatBtn = document.getElementById('clear-chat');
    const sidebar = document.querySelector('.sidebar');
    const suggestions = document.getElementById('suggestions');
    const subjectInfo = document.getElementById('subject-info');
    
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
    let messageCount = 0;
    
    // Connect to WebSocket
    socket.on('connect', function() {
        console.log('Connected to server');
        clearTimeout(connectionTimeout);
        
        // Remove any connection error messages
        const connectionError = document.querySelector('.connection-error');
        if (connectionError) {
            connectionError.remove();
        }
        
        // Show connection status
        showSystemMessage('Connected to Learning Agent', 'success');
    });
    
    // Set a connection timeout
    connectionTimeout = setTimeout(function() {
        if (!socket.connected) {
            console.error('Connection timeout');
            showSystemMessage('Connection timeout. Please check if the server is running and refresh the page.', 'error');
        }
    }, 5000);
    
    // Handle incoming messages
    socket.on('message', function(data) {
        removeTypingIndicator();
        isWaitingForResponse = false;
        messageCount++;
        
        // Map 'agent' role to 'assistant' for consistent styling
        const role = data.role === 'agent' ? 'assistant' : data.role;
        addMessage(role, data.content);
        scrollToBottom();
        
        // Hide suggestions after first interaction
        if (messageCount > 1 && suggestions) {
            suggestions.style.display = 'none';
        }
    });
    
    // Handle disconnection
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        showSystemMessage('Disconnected from server. Please refresh the page.', 'error');
        isWaitingForResponse = false;
    });
    
    // Handle connection errors
    socket.on('connect_error', function(error) {
        console.error('Connection error:', error);
        showSystemMessage('Failed to connect to server. Please check if the server is running and refresh the page.', 'error');
        isWaitingForResponse = false;
    });
    
    // Handle reconnection attempts
    socket.on('reconnect_attempt', function(attemptNumber) {
        console.log(`Attempting to reconnect (${attemptNumber})`);
        showSystemMessage(`Reconnecting... (attempt ${attemptNumber})`, 'warning');
    });
    
    // Handle successful reconnection
    socket.on('reconnect', function(attemptNumber) {
        console.log(`Reconnected after ${attemptNumber} attempts`);
        showSystemMessage('Reconnected to server.', 'success');
    });
    
    // Handle reconnection errors
    socket.on('reconnect_error', function(error) {
        console.error('Reconnection error:', error);
    });
    
    // Handle reconnection failure
    socket.on('reconnect_failed', function() {
        console.error('Failed to reconnect');
        showSystemMessage('Failed to reconnect to server. Please refresh the page.', 'error');
    });
    
    // Handle errors
    socket.on('error', function(error) {
        console.error('Socket error:', error);
        showSystemMessage('An error occurred with the connection. Please refresh the page.', 'error');
        isWaitingForResponse = false;
    });
    
    // Handle form submission
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (message && !isWaitingForResponse) {
            sendMessage(message);
        } else if (isWaitingForResponse) {
            showSystemMessage('Please wait for the current response to complete.', 'warning');
        }
    });
    
    // Function to send a message
    function sendMessage(message) {
        // Clear input field
        userInput.value = '';
        
        // Add user message to chat
        addMessage('user', message);
        
        // Show typing indicator
        addTypingIndicator();
        
        // Hide suggestions after first message
        if (suggestions) {
            suggestions.style.display = 'none';
        }
        
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
                    showSystemMessage('No response received. Please try again.', 'error');
                }
            }, 30000); // 30 seconds timeout
        } catch (error) {
            console.error('Error sending message:', error);
            removeTypingIndicator();
            showSystemMessage('Failed to send message. Please try again.', 'error');
        }
        
        // Scroll to bottom
        scrollToBottom();
    }
    
    // Function to add a message to the chat
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        
        if (role === 'user') {
            messageDiv.classList.add('user-message');
            messageDiv.innerHTML = `
                <div class="message-content">
                    <i class="fas fa-user-circle" style="margin-right: 8px; color: rgba(255,255,255,0.8);"></i>
                    ${escapeHtml(content)}
                </div>
                <div class="message-time">${getCurrentTime()}</div>
            `;
        } else if (role === 'assistant' || role === 'agent') {
            messageDiv.classList.add('agent-message');
            messageDiv.innerHTML = `
                <div class="message-content">
                    <i class="fas fa-robot" style="margin-right: 8px; color: var(--primary-color);"></i>
                    ${formatAgentMessage(content)}
                </div>
                <div class="message-time">${getCurrentTime()}</div>
            `;
        } else {
            messageDiv.classList.add('system-message');
            messageDiv.innerHTML = `
                <div class="message-content">
                    <i class="fas fa-info-circle" style="margin-right: 8px;"></i>
                    ${escapeHtml(content)}
                </div>
            `;
        }
        
        chatMessages.appendChild(messageDiv);
        
        // Animate the message appearance
        setTimeout(() => {
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 10);
    }
    
    // Function to show system messages with different types
    function showSystemMessage(content, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'system-message');
        
        let icon = 'fas fa-info-circle';
        if (type === 'success') icon = 'fas fa-check-circle';
        else if (type === 'warning') icon = 'fas fa-exclamation-triangle';
        else if (type === 'error') icon = 'fas fa-times-circle';
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <i class="${icon}" style="margin-right: 8px;"></i>
                ${escapeHtml(content)}
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
        
        // Auto-remove system messages after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
    
    // Function to add typing indicator
    function addTypingIndicator() {
        // Remove any existing typing indicators
        removeTypingIndicator();
        
        // Create typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('typing-indicator', 'message');
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
        // Aggressive cleanup of excessive spacing
        let formatted = content
            // Remove all excessive line breaks (more than 1)
            .replace(/\n{2,}/g, '\n')
            // Remove trailing/leading whitespace from each line
            .replace(/^[ \t]+|[ \t]+$/gm, '')
            // Remove empty lines completely
            .replace(/^\s*\n/gm, '')
            // Normalize multiple spaces to single space
            .replace(/ {2,}/g, ' ')
            // Remove spaces around line breaks
            .replace(/\s*\n\s*/g, '\n')
            // Trim the entire content
            .trim();
        
        // Process emojis to make them more visible
        formatted = formatted.replace(/([\u{1F300}-\u{1F6FF}])/gu, '<span class="emoji">$1</span>');
        
        // Convert markdown-style formatting to HTML
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/##\s+([^\n]+)/g, '<h2>$1</h2>');
        formatted = formatted.replace(/###\s+([^\n]+)/g, '<h3>$1</h3>');
        formatted = formatted.replace(/#\s+([^\n]+)/g, '<h1>$1</h1>');
        formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Handle bullet points more carefully
        formatted = formatted.replace(/^\s*[-•]\s+(.+)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/^\s*\d+\.\s+(.+)$/gm, '<li>$1</li>');
        
        // Wrap consecutive list items in ul tags
        formatted = formatted.replace(/(<li>.*?<\/li>)(\s*<li>.*?<\/li>)*/gs, function(match) {
            return '<ul>' + match.replace(/\s+/g, ' ') + '</ul>';
        });
        
        // Split content into lines and process each
        const lines = formatted.split('\n').filter(line => line.trim().length > 0);
        
        // Group lines into paragraphs and lists
        const elements = [];
        let currentParagraph = [];
        
        for (let line of lines) {
            line = line.trim();
            if (!line) continue;
            
            // If it's already HTML (contains tags), add it directly
            if (line.includes('<') && line.includes('>')) {
                if (currentParagraph.length > 0) {
                    elements.push(`<p>${currentParagraph.join(' ')}</p>`);
                    currentParagraph = [];
                }
                elements.push(line);
            } else {
                // Add to current paragraph
                currentParagraph.push(line);
            }
        }
        
        // Add any remaining paragraph
        if (currentParagraph.length > 0) {
            elements.push(`<p>${currentParagraph.join(' ')}</p>`);
        }
        
        // Join all elements with minimal spacing
        formatted = elements.join('');
        
        // Clean up any double-escaped HTML entities
        formatted = formatted.replace(/&amp;lt;/g, '&lt;');
        formatted = formatted.replace(/&amp;gt;/g, '&gt;');
        
        // Final aggressive cleanup: remove all unnecessary whitespace
        formatted = formatted
            .replace(/>\s+</g, '><')  // Remove spaces between tags
            .replace(/\s+/g, ' ')     // Normalize all whitespace to single spaces
            .replace(/\s+>/g, '>')    // Remove spaces before closing tags
            .replace(/<\s+/g, '<')    // Remove spaces after opening tags
            .trim();
        
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
    
    // Function to get current time
    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
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
                const subjectName = this.querySelector('span').textContent;
                const activeClass = document.querySelector('.class-btn.active').textContent;
                updateSubjectInfo(activeClass, subjectName);
                
                // Add a system message about subject change
                showSystemMessage(`Switched to ${subjectName} for Class ${activeClass}`, 'success');
                
                // Update topic pills based on subject
                updateTopicPills(subjectName);
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
                const activeSubject = document.querySelector('.subject-btn.active span').textContent;
                updateSubjectInfo(className, activeSubject);
                
                // Add a system message about class change
                showSystemMessage(`Switched to Class ${className} for ${activeSubject}`, 'success');
            });
        });
        
        // Topic pill click handlers
        topicPills.forEach(pill => {
            pill.addEventListener('click', function() {
                const topicName = this.textContent;
                userInput.value = `Tell me about ${topicName}`;
                userInput.focus();
                
                // Add visual feedback
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            });
        });
        
        // Suggestion button click handlers
        suggestionButtons.forEach(button => {
            button.addEventListener('click', function() {
                const question = this.getAttribute('data-question');
                if (question) {
                    sendMessage(question);
                }
                
                // Add visual feedback
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            });
        });
        
        // Toggle sidebar functionality
        if (toggleSidebarBtn) {
            toggleSidebarBtn.addEventListener('click', function() {
                sidebar.classList.toggle('collapsed');
                
                // Update icon
                const icon = this.querySelector('i');
                if (sidebar.classList.contains('collapsed')) {
                    icon.className = 'fas fa-chevron-right';
                } else {
                    icon.className = 'fas fa-bars';
                }
            });
        }
        
        // Clear chat functionality
        if (clearChatBtn) {
            clearChatBtn.addEventListener('click', function() {
                if (confirm('Are you sure you want to clear the chat?')) {
                    chatMessages.innerHTML = '';
                    messageCount = 0;
                    
                    // Show suggestions again
                    if (suggestions) {
                        suggestions.style.display = 'block';
                    }
                    
                    // Add welcome message
                    setTimeout(() => {
                        addMessage('assistant', 'Chat cleared! How can I help you with your studies today?');
                    }, 500);
                }
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + K to focus input
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                userInput.focus();
            }
            
            // Escape to clear input
            if (e.key === 'Escape') {
                userInput.value = '';
                userInput.blur();
            }
        });
    }
    
    // Helper functions
    function updateSubjectInfo(className, subjectName) {
        if (subjectInfo) {
            subjectInfo.textContent = `CBSE Class ${className} ${subjectName} Tutor`;
        }
    }
    
    function updateTopicPills(subjectName) {
        const topicData = {
            'Physics': ['Motion', 'Forces', 'Energy', 'Waves', 'Electricity', 'Magnetism'],
            'Chemistry': ['Atoms', 'Molecules', 'Reactions', 'Acids', 'Bases', 'Organic'],
            'Math': ['Algebra', 'Geometry', 'Calculus', 'Statistics', 'Trigonometry', 'Probability'],
            'Biology': ['Cells', 'Genetics', 'Evolution', 'Ecology', 'Anatomy', 'Physiology']
        };
        
        const topics = topicData[subjectName] || topicData['Physics'];
        const topicContainer = document.querySelector('.topic-pills');
        
        if (topicContainer) {
            topicContainer.innerHTML = '';
            topics.forEach(topic => {
                const pill = document.createElement('span');
                pill.className = 'topic-pill';
                pill.setAttribute('data-topic', topic);
                pill.textContent = topic;
                pill.addEventListener('click', function() {
                    const topicName = this.textContent;
                    userInput.value = `Tell me about ${topicName}`;
                    userInput.focus();
                    
                    // Add visual feedback
                    this.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        this.style.transform = '';
                    }, 150);
                });
                topicContainer.appendChild(pill);
            });
        }
    }
    
    // Focus input field on load
    userInput.focus();
    
    // Add initial welcome message
    setTimeout(() => {
        addMessage('assistant', '🎓 Welcome to your Learning Agent! I\'m here to help you master physics concepts. You can:\n\n• Ask questions about any physics topic\n• Use the sidebar to switch subjects and classes\n• Click on topic pills for quick questions\n• Try the suggested questions below\n\nWhat would you like to learn about today?');
    }, 1000);
});
