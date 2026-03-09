document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth()) return;
    await loadUserInfo();
    await fetchHistory();

    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const btnClear = document.getElementById('btnClearChat');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;

        // Hiện tin nhắn user
        appendMessage('user', text);
        input.value = '';

        // Hiện typing indicator
        const typingId = showTypingIndicator();

        try {
            const res = await fetchWithAuth('/chat', {
                method: 'POST',
                body: JSON.stringify({ message: text })
            });

            removeMessage(typingId);

            if (res && res.ok) {
                const data = await res.json();
                appendMessage('assistant', data.message, data.image);
            } else {
                appendMessage('assistant', '⚠️ Lỗi: Không thể kết nối với AI Agent.');
            }
        } catch (error) {
            removeMessage(typingId);
            appendMessage('assistant', '⚠️ Lỗi: ' + error.message);
        }
    });

    btnClear.addEventListener('click', async () => {
        if (!confirm('Bạn có chắc muốn xóa lịch sử chat?')) return;
        const res = await fetchWithAuth('/chat/history', { method: 'DELETE' });
        if (res && res.ok) {
            document.getElementById('chat-messages').innerHTML = `
                <div class="message msg-assistant">
                    Lịch sử đã được xóa. Tôi có thể giúp gì thêm cho bạn?
                </div>
            `;
        }
    });
});

async function fetchHistory() {
    try {
        const res = await fetchWithAuth('/chat/history');
        if (res && res.ok) {
            const history = await res.json();
            const container = document.getElementById('chat-messages');

            // Xóa intro template ban đầu nếu có dữ liệu
            if (history.length > 0) {
                container.innerHTML = '';
                history.forEach(item => {
                    appendMessage(item.role, item.content);
                });
            }
        }
    } catch (err) {
        console.error("Failed to load chat history", err);
    }
}

function appendMessage(role, text, imageUrl = null) {
    const container = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role === 'user' ? 'msg-user' : 'msg-assistant'}`;

    // Convert markdown to HTML nếu là assistant
    let contentHtml = role === 'assistant' ? marked.parse(text) : text;

    // Nhét ảnh nếu có
    if (imageUrl) {
        // Cần truyền token nếu URL yêu cầu xác thực
        // Ta parse lại url nối thêm token
        const token = getAuthToken();
        const authedImageUrl = `http://localhost:8000${imageUrl}?token=${token}`;

        contentHtml += `<div class="mt-2 text-center">
            <img src="${authedImageUrl}" class="img-fluid rounded border border-cyan" style="max-height: 200px" alt="Camera Snapshot">
        </div>`;
    }

    msgDiv.innerHTML = contentHtml;
    container.appendChild(msgDiv);

    // Cuộn xuống cuối
    container.scrollTop = container.scrollHeight;
}

function showTypingIndicator() {
    const container = document.getElementById('chat-messages');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message msg-assistant typing-indicator';
    div.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}
