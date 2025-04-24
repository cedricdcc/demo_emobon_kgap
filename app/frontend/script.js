const serverBaseURL = "http://127.0.0.1:5000";

const messagesDiv = document.getElementById("messages");
const userInput = document.getElementById("user-input");
const sendButton = document.getElementById("send-button");

sendButton.addEventListener("click", () => {
  const userMessage = userInput.value.trim();
  if (userMessage) {
    addMessage("User", userMessage);
    userInput.value = "";
    fetchResponse(userMessage);
  }
});

function addMessage(sender, message) {
  const messageDiv = document.createElement("div");
  messageDiv.textContent = `${sender}: ${message}`;
  messagesDiv.appendChild(messageDiv);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function fetchResponse(userMessage) {
  try {
    const response = await fetch(`${serverBaseURL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage }),
    });
    const data = await response.json();
    addMessage("Bot", data.reply);
  } catch (error) {
    console.error("Error fetching response:", error);
    addMessage("Bot", "Error: Unable to fetch response.");
  }
}
