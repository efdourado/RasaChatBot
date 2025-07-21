document.addEventListener("DOMContentLoaded", () => {
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");
    const chatMessagesContainer = document.getElementById("chat-messages");
    const newChatButtonEl = document.querySelector(".new-chat-button");

    const sidebar = document.querySelector('.sidebar');
    const menuButton = document.querySelector('.menu-button');

    const attachButton = document.getElementById("attach-button");
    const attachmentOptions = document.getElementById("attachment-options");
    const fileUploadInput = document.getElementById("file-upload");

    const transferButton = document.getElementById('request-transfer-btn');

    const rasaServerUrl = "http://localhost:5005/webhooks/rest/webhook";

    if (menuButton && sidebar) {
        menuButton.addEventListener('click', () => {
            sidebar.classList.toggle('expanded');
        });
    }

    attachButton.addEventListener("click", () => {
        attachmentOptions.classList.toggle("visible");
    });

    fileUploadInput.addEventListener("change", (event) => {
        const file = event.target.files[0];
        if (file) {
            const fileInfoText = `Arquivo selecionado: <strong>${file.name}</strong>`;
            appendMessage(fileInfoText, "user");
            console.log("Arquivo selecionado:", file);
        }
        attachmentOptions.classList.remove("visible");
        fileUploadInput.value = '';
    });

    document.addEventListener("click", (event) => {
        if (!attachmentOptions.contains(event.target) && !attachButton.contains(event.target)) {
            attachmentOptions.classList.remove("visible");
        }
    });

    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        let newHeight = userInput.scrollHeight;
        const maxHeight = parseInt(getComputedStyle(userInput).maxHeight);

        if (newHeight > maxHeight) {
            newHeight = maxHeight;
            userInput.style.overflowY = 'auto';
        } else {
            userInput.style.overflowY = 'hidden';
        }
        userInput.style.height = newHeight + 'px';
    });

    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    }

    function createMessageBlock(text, sender, imageUrl = null, buttons = null) {
        const messageBlock = document.createElement("div");
        messageBlock.classList.add("message-block", sender === "user" ? "user-message-block" : "bot-message-block");

        if (sender === "bot") {
            const avatar = document.createElement("div");
            avatar.classList.add("message-avatar", "bot-avatar");
            avatar.textContent = "CV";
            messageBlock.appendChild(avatar);
        }

        const contentWrapper = document.createElement("div");
        contentWrapper.classList.add("message-content-wrapper");

        const senderName = document.createElement("div");
        senderName.classList.add("message-sender-name");
        senderName.textContent = sender === "user" ? "Você" : "Clínica Vértice";
        contentWrapper.appendChild(senderName);

        const bubble = document.createElement("div");
        bubble.classList.add("message-bubble");

        if (text) {
            bubble.innerHTML = text.replace(/\n/g, '<br>');
        }

        if (imageUrl) {
            const img = document.createElement("img");
            img.src = imageUrl;
            img.alt = "Imagem enviada";
            img.classList.add("bot-image");
            bubble.appendChild(img);
        }
        contentWrapper.appendChild(bubble);

        if (buttons && buttons.length > 0) {
            const buttonsDiv = document.createElement("div");
            buttonsDiv.classList.add("bot-buttons");
            buttons.forEach((buttonInfo) => {
                const btn = document.createElement("button");
                btn.textContent = buttonInfo.title;
                btn.classList.add("chat-button");
                btn.addEventListener("click", () => {
                    appendMessage(buttonInfo.title, "user");
                    sendMessageToRasaAPI(buttonInfo.payload);
                });
                buttonsDiv.appendChild(btn);
            });
            contentWrapper.appendChild(buttonsDiv);
        }

        const timestamp = document.createElement("div");
        timestamp.classList.add("message-timestamp");
        timestamp.textContent = getCurrentTime();
        contentWrapper.appendChild(timestamp);

        messageBlock.appendChild(contentWrapper);
        return messageBlock;
    }

    function appendMessage(text, sender, imageUrl = null, buttons = null) {
        if (!chatMessagesContainer) return;
        const messageElement = createMessageBlock(text, sender, imageUrl, buttons);
        chatMessagesContainer.appendChild(messageElement);
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    }

    async function sendMessageToRasaAPI(messageText) {
        if (!messageText && messageText !== 0) return;

        try {
            const response = await fetch(rasaServerUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ sender: "user_id_example", message: messageText }),
            });

            if (!response.ok) {
                let errorData = { message: "Erro desconhecido na resposta." };
                try { errorData = await response.json(); } catch (e) { }
                const errorMessageDetail = errorData?.message || errorData?.reason || response.statusText;
                throw new Error(`HTTP error! status: ${response.status} - ${errorMessageDetail}`);
            }

            const botResponses = await response.json();

            if (botResponses && botResponses.length > 0) {
                botResponses.forEach((botMsg, index) => {
                    setTimeout(() => {
                        appendMessage(botMsg.text, "bot", botMsg.image, botMsg.buttons);
                    }, 200 * (index + 1));
                });
            } else if (typeof messageText === 'string' && !messageText.startsWith("/")) {
                console.warn("Rasa_API: Resposta vazia recebida para:", messageText)
            }

        } catch (error) {
            console.error("Erro ao enviar mensagem para o Rasa:", error);
            appendMessage("Desculpe, estou com problemas para me conectar. Tente novamente mais tarde.", "bot");
        }
    }

    function handleSend() {
        const messageText = userInput.value.trim();
        if (messageText) {
            appendMessage(messageText, "user");
            sendMessageToRasaAPI(messageText);
            userInput.value = "";
            userInput.style.height = 'auto';
            userInput.style.overflowY = 'hidden';
            userInput.focus();
        }
    }

    if (sendButton) sendButton.addEventListener("click", handleSend);

    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            handleSend();
        }
    });

    if (newChatButtonEl) {
        newChatButtonEl.addEventListener("click", () => {
            if (chatMessagesContainer) chatMessagesContainer.innerHTML = '';
            sendMessageToRasaAPI('/session_start');
            userInput.focus();
            document.querySelectorAll('.conversation-list .conversation-item.active').forEach(item => {
                item.classList.remove('active');
            });
        });
    }

    if (transferButton) {
        transferButton.addEventListener('click', () => {
            const userMessage = "Gostaria de falar com um atendente";
            const payload = "/request_human_handover";

            appendMessage(userMessage, "user");
            sendMessageToRasaAPI(payload);

            setTimeout(() => {
                appendMessage("Ok, estou buscando um atendente para você. Por favor, aguarde um momento.", "bot");
            }, 300);
        });
    }

    function updateSupportStatus() {
        const statusDot = document.getElementById('support-status-dot');
        const statusText = document.getElementById('support-status-text');
        if (!statusDot || !statusText || !transferButton) return;

        const now = new Date();
        const day = now.getDay();
        const hour = now.getHours();

        const isOnline = (day >= 1 && day <= 5 && hour >= 8 && hour < 18);

        if (isOnline) {
            statusDot.classList.remove('offline');
            statusDot.classList.add('online');
            statusText.textContent = 'Atendentes disponíveis';
            transferButton.disabled = false;
        } else {
            statusDot.classList.remove('online');
            statusDot.classList.add('offline');
            statusText.textContent = 'Fora do horário de atendimento';
            transferButton.disabled = true;
        }
    }

    window.handleQuickAction = function(message) {
        event.preventDefault();
        appendMessage(message, "user");
        sendMessageToRasaAPI(message);
        userInput.focus();
    }

    function initializeChat() {
        appendMessage("Olá! Bem-vindo(a) ao assistente virtual da Clínica Vértice. Como posso ajudar?", "bot", null, [
            { title: "Marcar Consulta", payload: "/informar_agendamento" },
            { title: "Ver Resultados", payload: "/informar_resultados" }
        ]);
        userInput.focus();

        updateSupportStatus();
        setInterval(updateSupportStatus, 60000);
    }

    initializeChat();
});