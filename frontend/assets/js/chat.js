/**
 * chat.js — AI Chat logic
 * - Load history từ backend
 * - Gửi message qua POST /chat (cookie auth)
 * - Typing indicator
 * - Enter để gửi, Shift+Enter xuống dòng
 * - Auto-scroll
 */

const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("send");
const clearBtn = document.getElementById("clearBtn");

// ── Startup ──────────────────────────────────

document.addEventListener("DOMContentLoaded", async () => {
  await loadNavbar();
  await loadHistory();

  // Enter to send
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-resize textarea
  inputEl.addEventListener("input", () => {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + "px";
  });

  sendBtn.addEventListener("click", sendMessage);

  clearBtn.addEventListener("click", async () => {
    if (!confirm("Xóa toàn bộ lịch sử chat?")) return;
    try {
      await api("/chat/history", { method: "DELETE" });
      messagesEl.innerHTML = "";
      appendBotMessage("Lịch sử đã được xóa. Xin chào! Tôi có thể giúp gì cho bạn về tình trạng giao thông hôm nay?");
    } catch { }
  });
});

// ── Load history ──────────────────────────────

async function loadHistory() {
  try {
    const history = await api("/chat/history");
    if (!history || history.length === 0) {
      appendBotMessage("Xin chào! 👋 Tôi là AI Traffic Assistant.\nBạn có thể hỏi tôi về tình trạng giao thông trên các tuyến đường đang được giám sát.");
      return;
    }
    history.forEach((item) => {
      if (item.role === "user") {
        appendUserMessage(item.content, new Date(item.created_at));
      } else {
        appendBotMessage(item.content, new Date(item.created_at));
      }
    });
    scrollToBottom();
  } catch (e) {
    appendBotMessage("Xin chào! Không tải được lịch sử chat. Hãy thử hỏi tôi điều gì đó.");
  }
}

// ── Send Message ──────────────────────────────

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;

  inputEl.value = "";
  inputEl.style.height = "auto";
  sendBtn.disabled = true;

  appendUserMessage(text);
  const typingEl = appendTyping();
  scrollToBottom();

  try {
    const data = await api("/chat", {
      method: "POST",
      body: JSON.stringify({ message: text }),
    });
    typingEl.remove();
    appendBotMessage(data.message || "Xin lỗi, tôi không hiểu câu hỏi này.");
  } catch (e) {
    typingEl.remove();
    appendBotMessage(`❌ Lỗi: ${e.message}`);
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
    scrollToBottom();
  }
}

// ── DOM Helpers ───────────────────────────────

function appendUserMessage(text, date) {
  const div = document.createElement("div");
  div.className = "msg user";
  div.innerHTML = `
    <div class="msg-avatar">👤</div>
    <div>
      <div class="msg-bubble">${escapeHtml(text)}</div>
      <div class="msg-time">${fmtTime(date)}</div>
    </div>
  `;
  messagesEl.appendChild(div);
  return div;
}

function appendBotMessage(text, date) {
  const div = document.createElement("div");
  div.className = "msg bot";
  div.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div>
      <div class="msg-bubble">${escapeHtml(text)}</div>
      <div class="msg-time">${fmtTime(date)}</div>
    </div>
  `;
  messagesEl.appendChild(div);
  return div;
}

function appendTyping() {
  const div = document.createElement("div");
  div.className = "typing-indicator";
  div.innerHTML = `
    <div class="msg-avatar" style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,rgba(56,189,248,0.2),rgba(129,140,248,0.2));border:1px solid rgba(56,189,248,0.25);display:flex;align-items:center;justify-content:center;font-size:14px;">🤖</div>
    <div class="typing-dots">
      <span></span><span></span><span></span>
    </div>
  `;
  messagesEl.appendChild(div);
  return div;
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/\n/g, "<br>");
}