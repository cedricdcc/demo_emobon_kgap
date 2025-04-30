const serverBaseURL = "http://localhost:5000";

const messagesDiv = document.getElementById("messages");
const userInput = document.getElementById("user-input");
const sendButton = document.getElementById("send-button");

let currentMessage = ""; // Variable to store the full message being constructed

sendButton.addEventListener("click", () => {
  const userMessage = userInput.value.trim();
  if (userMessage) {
    const uniqueId = `msg-${Date.now()}`;
    addMessage("User", userMessage, uniqueId);
    userInput.value = "";
    fetchResponse(userMessage, uniqueId);
  }
});

function addMessage(sender, message, id = null) {
  const messageDiv = document.createElement("div");
  messageDiv.textContent = message;

  // Apply appropriate CSS class based on sender
  if (sender === "User") {
    messageDiv.classList.add("message-human");
  } else if (sender === "Bot") {
    messageDiv.classList.add("message-chatbot");
  }

  if (id) {
    messageDiv.id = id;
  }
  messagesDiv.appendChild(messageDiv);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  if (sender === "Bot") {
    messageDiv.classList.add("message-chatbot");
    messagesDiv.scrollTop = messagesDiv.scrollHeight; // Scroll to the bottom for bot messages
  }
}

async function fetchResponse(userMessage, uniqueId) {
  try {
    const response = await fetch(`${serverBaseURL}/users/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage }),
    });

    if (!response.body) {
      throw new Error("ReadableStream not supported.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let botMessageDiv = null;

    let errorCount = 0; // Counter for consecutive errors
    while (true) {
      const { done, value } = await reader.read();

      const chunk = decoder.decode(value, { stream: true });
      //console.log("Received chunk:", chunk); // Log the received chunk for debugging

      try {
        const parsedChunk = parseChunk(chunk);

        if (done || parsedChunk.done) break; // Exit loop if done

        if (parsedChunk.reply) {
          currentMessage += parsedChunk.reply; // Append only the "reply" part to currentMessage
          const replyHTML = convertMarkdownToHTML(currentMessage); // Convert concatenated replies to HTML

          if (!botMessageDiv) {
            botMessageDiv = document.createElement("div");
            botMessageDiv.id = `bot-${uniqueId}`;
            botMessageDiv.innerHTML = `<b>EMOBON-Agent</b> ${replyHTML}`;
            botMessageDiv.classList.add("message-chatbot");
            messagesDiv.appendChild(botMessageDiv);
          } else {
            botMessageDiv.innerHTML = `<bEMOBON-Agent</b> ${replyHTML}`;
            botMessageDiv.classList.add("message-chatbot");
          }

          messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        // Reset error count on successful parse
        errorCount = 0;
      } catch (error) {
        console.error("Error parsing chunk:", error);
        errorCount++;

        // Exit loop if error count exceeds 10
        if (errorCount >= 10) {
          console.error("Too many consecutive errors. Exiting loop.");
          break;
        }
      }
    }
  } catch (error) {
    console.error("Error fetching response:", error);
    addMessage("Bot", "Error: Unable to fetch response.");
  }
}

function convertMarkdownToHTML(markdown) {
  try {
    const parser = new showdown.Converter();
    return parser.makeHtml(markdown);
  } catch (error) {
    console.error("Error converting Markdown to HTML:", error);
    return null;
  }
}
function parseChunk(chunk) {
  try {
    return JSON.parse(chunk);
  } catch (error) {
    throw new Error("Invalid JSON format in chunk.");
  }
}
