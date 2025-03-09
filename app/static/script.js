document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chatMessages');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const sessionId = 'session-' + Math.random().toString(36).substring(7);

    // Vis velkomstmelding
    addBotMessage("Hei! Jeg er RiksTVs digitale assistent. Hvordan kan jeg hjelpe deg i dag?");

    // Send melding når brukeren klikker på send-knappen
    sendButton.addEventListener('click', sendMessage);

    // Send melding når brukeren trykker Enter
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            // Vis brukerens melding
            addUserMessage(message);
            messageInput.value = '';

            // Vis "skriver" indikator
            showTypingIndicator();

            // Send melding til API
            fetch('http://127.0.0.1:8000/chat', {  // 🔥 Endret fra 8080 til 8000, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId
                })
            })
            .then(response => response.json())
            .then(data => {
                // Fjern "skriver" indikator
                removeTypingIndicator();
                
                // Vis botens svar
                addBotMessage(data.response);

                // Hvis det finnes trinnvise instruksjoner, vis dem
                if (data.steps && data.steps.length > 0) {
                    const stepsList = document.createElement('ul');
                    stepsList.className = 'steps-list';
                    data.steps.forEach(step => {
                        const li = document.createElement('li');
                        li.textContent = step;
                        stepsList.appendChild(li);
                    });
                    chatMessages.lastElementChild.appendChild(stepsList);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                removeTypingIndicator();
                addBotMessage("Beklager, jeg opplevde en teknisk feil. Vennligst prøv igjen.");
            });
        }
    }

    function addUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function addBotMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = chatMessages.querySelector('.typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
}); 