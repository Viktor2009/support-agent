const API_BASE = window.location.origin;
const SESSION_KEY = "support_agent_session_id";
const CUSTOMER_ID = new URLSearchParams(window.location.search).get("customer_id") || "cust_456";

const messagesEl = document.getElementById("messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const statusEl = document.getElementById("status");

function getSessionId() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = "widget-" + crypto.randomUUID().slice(0, 8);
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

function addMessage(text, role) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendMessage(text) {
  addMessage(text, "user");
  input.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: getSessionId(),
        message: text,
        customer_id: CUSTOMER_ID,
      }),
    });

    const data = await response.json();

    if (data.status === "awaiting_operator") {
      statusEl.textContent = "ожидание оператора";
      statusEl.style.color = "#d97706";
      addMessage("Оператор подключается. Пожалуйста, подождите.", "system");
      return;
    }

    addMessage(data.answer || "Нет ответа", "bot");
  } catch (err) {
    addMessage("Ошибка соединения с сервером.", "system");
  } finally {
    input.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  sendMessage(text);
});

addMessage("Здравствуйте! Чем могу помочь?", "bot");
