document.addEventListener('DOMContentLoaded', async () => {
    // 1. Kiểm tra xác thực và load user info
    const token = requireAuth();
    if (!token) return;
    await loadUserInfo();

    // 2. Fetch danh sách tuyến đường
    await loadRoads();
});

// Cache connections để clear khi cần
const activeWebSockets = [];

async function loadRoads() {
    const spinner = document.getElementById('loading-spinner');
    const grid = document.getElementById('roads-grid');

    try {
        const res = await fetchWithAuth('/roads');
        if (!res || !res.ok) throw new Error("Failed to load roads");

        const data = await res.json();
        const roadNames = data.road_names || [];

        // Xóa spinner
        if (spinner) spinner.remove();

        if (roadNames.length === 0) {
            grid.innerHTML = '<div class="col-12 text-center text-muted py-5">Chưa có tuyến đường nào được cấu hình.</div>';
            return;
        }

        // Tạo card cho từng tuyến đường
        roadNames.forEach(road => {
            createRoadCard(road, grid);
            connectWebSocket(road);
        });

    } catch (err) {
        console.error(err);
        grid.innerHTML = '<div class="col-12 text-center text-danger py-5"><i class="fa-solid fa-triangle-exclamation fa-2x mb-3"></i><br>Không thể tải dữ liệu từ máy chủ.</div>';
    }
}

function createRoadCard(roadName, container) {
    const template = document.getElementById('road-card-template').content.cloneNode(true);

    // Gán ID cho DOM node để dễ query khi update WS
    const wrapper = template.querySelector('.col-12');
    wrapper.id = `card-${CSS.escape(roadName)}`;

    // Set Tên đường
    template.querySelector('.road-title').textContent = roadName;

    container.appendChild(template);
}

function connectWebSocket(roadName) {
    const token = getAuthToken();
    const safeRoadName = encodeURIComponent(roadName);
    const cardId = `#card-${CSS.escape(roadName)}`;
    const cardEl = document.querySelector(cardId);
    if (!cardEl) return;

    // 1. WS Stream Frames (Video)
    const wsFramesUrl = `ws://localhost:8000/api/v1/ws/roads/${safeRoadName}/frames?token=${token}`;
    const wsFrames = new WebSocket(wsFramesUrl);
    // Nhận dữ liệu ảnh dưới dạng Blob
    wsFrames.binaryType = "blob";

    wsFrames.onmessage = (event) => {
        const imgEl = cardEl.querySelector('.road-video-stream');
        // Tạo URL object từ binary blob
        const url = URL.createObjectURL(event.data);
        // Giải phóng bộ nhớ ảnh frame cũ
        imgEl.onload = () => URL.revokeObjectURL(url);
        imgEl.src = url;

        // Ẩn màng hình mất kết nối nếu có
        cardEl.querySelector('.reconnect-overlay').classList.add('d-none');
    };

    wsFrames.onerror = () => {
        cardEl.querySelector('.reconnect-overlay').classList.remove('d-none');
    };

    wsFrames.onclose = () => {
        console.warn(`[${roadName}] Frame WS closed`);
    };

    // 2. WS Stream Info (Metrics)
    const wsInfoUrl = `ws://localhost:8000/api/v1/ws/roads/${safeRoadName}/info?token=${token}`;
    const wsInfo = new WebSocket(wsInfoUrl);

    wsInfo.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            updateCardMetrics(cardEl, data);
        } catch (e) {
            console.error("Parse JSON error", e);
        }
    };

    activeWebSockets.push(wsFrames, wsInfo);
}

function updateCardMetrics(cardEl, data) {
    // Nếu rỗng
    if (!data || Object.keys(data).length === 0) return;

    // Cập nhật số liệu Ô tô
    cardEl.querySelector('.count-car').textContent = data.count_car || 0;
    cardEl.querySelector('.speed-car').textContent = `${data.speed_car || 0} km/h`;

    // Cập nhật số liệu Xe máy
    cardEl.querySelector('.count-motor').textContent = data.count_motor || 0;
    cardEl.querySelector('.speed-motor').textContent = `${data.speed_motor || 0} km/h`;

    // Cập nhật Badge Trạng thái Mật độ
    const badgeEl = cardEl.querySelector('.road-status-badge');
    const density = data.density_status || "Không rõ";
    badgeEl.textContent = density;

    // Đổi màu badge
    badgeEl.className = 'badge rounded-pill road-status-badge ';
    if (density === "Thông thoáng") badgeEl.classList.add('bg-success', 'bg-opacity-75');
    else if (density === "Đông đúc") badgeEl.classList.add('bg-warning', 'text-dark');
    else if (density === "Tắc nghẽn") badgeEl.classList.add('bg-danger', 'pulse-glow');
    else badgeEl.classList.add('bg-secondary');

    // Insight tốc độ
    const insightEl = cardEl.querySelector('.speed-status');
    const speedStatus = data.speed_status || "-";
    insightEl.textContent = speedStatus;

    if (speedStatus === "Nhanh chóng") insightEl.className = "speed-status small fw-medium text-green";
    else if (speedStatus === "Chậm chạp") insightEl.className = "speed-status small fw-medium text-warning";
    else insightEl.className = "speed-status small fw-medium text-muted";
}

// Dọn dẹp memory leak khi đóng tab
window.addEventListener('beforeunload', () => {
    activeWebSockets.forEach(ws => {
        if (ws.readyState === WebSocket.OPEN) ws.close();
    });
});
