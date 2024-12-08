
let conversationHistory = [];

function displayConversation() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '';
    conversationHistory.forEach(message => {
        const messageDiv = document.createElement('div');
        messageDiv.className = message.startsWith('User:') ? 'user-message' : 'bot-message';
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
    });
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendMessage() {
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');

    if (userInput.value.trim() === '') return;

    // Add user message to chat
    conversationHistory.push(`User: ${userInput.value}`);
    displayConversation();

    // Send message to server
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userInput.value }),
    })
    .then(response => response.json())
    .then(data => {
        // Update conversation history with server response
        conversationHistory = data.conversation;
        displayConversation();
    })
    .catch(error => {
        console.error('Error:', error);
        conversationHistory.push('Assistant: Sorry, there was an error processing your request.');
        displayConversation();
    });

    userInput.value = '';
}

// Allow sending message with Enter key
document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Initialize the chat interface
displayConversation();