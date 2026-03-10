/**
 * websocket.js — WebSocket helpers for road frames & info streaming
 * 
 * Gửi JWT token qua ?token=<jwt> query param (vì WS không hỗ trợ header).
 * Token được lấy từ localStorage qua getToken() (định nghĩa trong auth.js).
 */

/**
 * Kết nối WebSocket stream cho 1 tuyến đường và cập nhật card UI.
 * @param {string} road - Tên tuyến đường
 * @param {HTMLElement} card - Road card DOM element
 * @param {Function} onInfo - Callback nhận data info (để update chart)
 */
function connectRoadWS(road, card, onInfo) {
    const safeRoad = encodeURIComponent(road);
    const token = getToken(); // từ auth.js
    const tokenParam = token ? `?token=${token}` : "";

    // ── Frame stream ──
    const wsFrame = new WebSocket(
        `${CONFIG.WS_BASE}/traffic/ws/roads/${safeRoad}/frames${tokenParam}`
    );
    wsFrame.binaryType = "blob";

    wsFrame.onmessage = (event) => {
        const img = card.querySelector(".road-video");
        const url = URL.createObjectURL(event.data);
        img.onload = () => URL.revokeObjectURL(url);
        img.src = url;
    };

    wsFrame.onerror = () => console.warn(`WS frames error: ${road}`);

    wsFrame.onclose = (e) => {
        if (e.code === 4001) { // custom: token invalid
            clearToken();
            goToLogin();
        }
    };

    // ── Info stream ──
    const wsInfo = new WebSocket(
        `${CONFIG.WS_BASE}/traffic/ws/roads/${safeRoad}/info${tokenParam}`
    );

    wsInfo.onmessage = (event) => {
        const data = JSON.parse(event.data);

        // Update stat pills
        const q = (sel) => card.querySelector(sel);
        if (q(".count-car")) q(".count-car").textContent = data.count_car ?? 0;
        if (q(".count-motor")) q(".count-motor").textContent = data.count_motor ?? 0;
        if (q(".speed-car")) q(".speed-car").textContent = `${data.speed_car ?? 0} km/h`;
        if (q(".speed-motor")) q(".speed-motor").textContent = `${data.speed_motor ?? 0} km/h`;

        // Status badge
        const badge = document.getElementById(`badge-${road}`);
        if (badge) updateStatusBadge(badge, data.density_status);

        // Callback để chart lấy data
        if (typeof onInfo === "function") onInfo(data, road);
    };

    wsInfo.onerror = () => console.warn(`WS info error: ${road}`);

    return { wsFrame, wsInfo };
}