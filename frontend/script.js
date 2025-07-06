document.addEventListener("DOMContentLoaded", () => {
  const userInput = document.getElementById("user-input");
  const sendButton = document.getElementById("send-button");
  const chatMessages = document.getElementById("chat-messages");
  
//  const rasaServerUrl = "https://chatbot-rasa-server-jax2.onrender.com/webhooks/rest/webhook";

  const rasaServerUrl = "http://localhost:5005/webhooks/rest/webhook";

  function addMessage(text, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add(
      "message",
      sender === "user" ? "user-message" : "bot-message"
    );
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  async function sendMessageToRasa(message) {
    try {
      const response = await fetch(rasaServerUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ sender: "user", message: message }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const botResponses = await response.json();
      botResponses.forEach((botMsg) => {
        if (botMsg.text) {
          addMessage(botMsg.text, "bot");
        }
        if (botMsg.image) {
          const img = document.createElement("img");
          img.src = botMsg.image;
          img.classList.add("bot-image");
          chatMessages.appendChild(img);
        }

        if (botMsg.buttons && botMsg.buttons.length > 0) {
          const buttonsDiv = document.createElement("div");
          buttonsDiv.classList.add("bot-buttons");
          botMsg.buttons.forEach((button) => {
            const btn = document.createElement("button");
            btn.textContent = button.title;
            btn.classList.add("chat-button");
            btn.addEventListener("click", () => {
              addMessage(button.title, "user");
              sendMessageToRasa(button.payload);
              buttonsDiv.remove();
            });
            buttonsDiv.appendChild(btn);
          });
          chatMessages.appendChild(buttonsDiv);
      } });
    } catch (error) {
      console.error("Error sending message to Rasa:", error);
      addMessage(
        "Desculpe, não consegui conectar ao servidor do chatbot.",
        "bot"
  ); } }

  sendButton.addEventListener("click", () => {
    const messageText = userInput.value.trim();
    if (messageText) {
      addMessage(messageText, "user");
      sendMessageToRasa(messageText);
      userInput.value = "";
  } });

  userInput.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
      sendButton.click();
} }); });