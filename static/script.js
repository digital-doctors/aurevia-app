const chat = document.getElementById("chat");
const sendBtn = document.getElementById("sendBtn");
const questionInput = document.getElementById("question");
const clearBtn = document.getElementById("clearChat");

function saveMessageToStorage(text, cls, time) {
  let history = JSON.parse(localStorage.getItem("chatHistory")) || [];
  history.push({ text, cls, time });
  localStorage.setItem("chatHistory", JSON.stringify(history));
}

function loadMessages() {
  let history = JSON.parse(localStorage.getItem("chatHistory")) || [];
  chat.innerHTML = "";
  history.forEach(m => addMessage(m.text, m.cls, m.time, false));
}

function clearMessages() {
  localStorage.removeItem("chatHistory");
  chat.innerHTML = "";
}

function addMessage(text, cls, time = null, save = true) {
  const msg = document.createElement("div");
  msg.className = "msg " + cls;
  msg.innerHTML = text;
  if (time) {
    const tspan = document.createElement("div");
    tspan.className = "msg-time";
    tspan.innerText = time;
    msg.appendChild(tspan);
  }
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;

  if (save && time) saveMessageToStorage(text, cls, time);
}

async function ask() {
  let question = questionInput.value.trim();
  if (!question) return;
  const subject = document.getElementById("subject").value;
  const difficulty = document.getElementById("difficulty").value;
  const userTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  addMessage(question, "user", userTime);

  questionInput.value = "";

  const typing = document.createElement("div");
  typing.className = "msg bot typing";
  const span = document.createElement("span");
  typing.appendChild(span);
  chat.appendChild(typing);
  chat.scrollTop = chat.scrollHeight;

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, subject, difficulty })
    });
    const data = await res.json();
    if (chat.contains(typing)) chat.removeChild(typing);
    addMessage(data.reply, "bot", data.time);
  } catch (err) {
    if (chat.contains(typing)) chat.removeChild(typing);
    const errTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    addMessage("Sorry, something went wrong. Please try again.", "bot", errTime);
    console.error(err);
  }
}

// ---- Event Listeners ----
sendBtn.addEventListener("click", ask);
questionInput.addEventListener("keypress", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    ask();
  }
});
clearBtn.addEventListener("click", clearMessages);

// Load messages on startup
window.onload = loadMessages;
