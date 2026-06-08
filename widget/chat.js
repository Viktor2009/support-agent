const API_BASE = window.location.origin;
const SESSION_KEY = "support_agent_session_id";
const CUSTOMER_ID = new URLSearchParams(window.location.search).get("customer_id") || "cust_456";
const API_KEY = new URLSearchParams(window.location.search).get("api_key") || "";
const TRANSPORT = new URLSearchParams(window.location.search).get("transport") || "sse";
const USE_STREAMING = new URLSearchParams(window.location.search).get("stream") !== "0";

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

function chatPayload(text) {
  return {
    session_id: getSessionId(),
    message: text,
    customer_id: CUSTOMER_ID,
  };
}

function addMessage(text, role) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

function handleStreamEvent(parsed, botDiv) {
  if (parsed.event === "token") {
    botDiv.textContent += parsed.data.text || "";
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return false;
  }
  if (parsed.event === "interrupt") {
    statusEl.textContent = "ожидание оператора";
    statusEl.style.color = "#d97706";
    addMessage("Оператор подключается. Пожалуйста, подождите.", "system");
    return true;
  }
  if (parsed.event === "done") {
    if (!botDiv.textContent && parsed.data.answer) {
      botDiv.textContent = parsed.data.answer;
    }
    return true;
  }
  if (parsed.event === "error") {
    throw new Error(parsed.data.detail || "stream error");
  }
  return false;
}

function parseSseBlock(block) {
  let event = "message";
  let data = "";
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      data += line.slice(5).trim();
    }
  }
  if (!data) return null;
  try {
    return { event, data: JSON.parse(data) };
  } catch {
    return null;
  }
}

async function sendMessageStream(text) {
  const botDiv = addMessage("", "bot");
  const headers = { "Content-Type": "application/json" };
  if (API_KEY) headers["X-API-Key"] = API_KEY;

  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify(chatPayload(text)),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";

    for (const block of blocks) {
      const parsed = parseSseBlock(block);
      if (!parsed) continue;
      if (handleStreamEvent(parsed, botDiv)) return;
    }
  }
}

function wsUrl() {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const params = new URLSearchParams();
  if (API_KEY) params.set("api_key", API_KEY);
  const qs = params.toString();
  return `${proto}//${window.location.host}/chat/ws${qs ? `?${qs}` : ""}`;
}

async function sendMessageWebSocket(text) {
  const botDiv = addMessage("", "bot");
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(wsUrl());

    socket.onopen = () => {
      socket.send(JSON.stringify(chatPayload(text)));
    };

    socket.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        if (handleStreamEvent(parsed, botDiv)) {
          socket.close();
          resolve();
        }
      } catch (err) {
        reject(err);
      }
    };

    socket.onerror = () => reject(new Error("WebSocket error"));
    socket.onclose = (event) => {
      if (event.code === 1008) reject(new Error("Unauthorized"));
    };
  });
}

async function sendMessageClassic(text) {
  const headers = { "Content-Type": "application/json" };
  if (API_KEY) headers["X-API-Key"] = API_KEY;

  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify(chatPayload(text)),
  });

  const data = await response.json();

  if (data.status === "awaiting_operator") {
    statusEl.textContent = "ожидание оператора";
    statusEl.style.color = "#d97706";
    addMessage("Оператор подключается. Пожалуйста, подождите.", "system");
    return;
  }

  addMessage(data.answer || "Нет ответа", "bot");
}

async function sendMessage(text) {
  addMessage(text, "user");
  input.disabled = true;

  try {
    if (TRANSPORT === "ws") {
      await sendMessageWebSocket(text);
    } else if (USE_STREAMING) {
      await sendMessageStream(text);
    } else {
      await sendMessageClassic(text);
    }
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
