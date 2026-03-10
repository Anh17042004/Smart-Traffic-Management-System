/**
 * utils.js — Shared UI utility functions
 */

/**
 * Tạo road card DOM element cho 1 tuyến đường.
 * @param {string} name - Tên tuyến đường
 * @returns {HTMLElement}
 */
function createRoadCard(name) {
    const card = document.createElement("div");
    card.className = "road-card";
    card.id = `card-${name}`;

    card.innerHTML = `
    <div class="road-video-wrap">
      <img class="road-video" alt="Camera ${name}">
      <div class="road-video-overlay">
        <div class="live-dot"></div>
        <span class="live-label">LIVE</span>
      </div>
    </div>
    <div class="road-body">
      <div class="road-name">
        <span>📍 ${name}</span>
        <span class="status-badge" id="badge-${name}">Loading...</span>
      </div>
      <div class="stats">
        <div class="stat-pill">
          <span class="stat-label">🚗 Ô tô</span>
          <span class="stat-value count-car">0</span>
          <span class="stat-sub speed-car">0 km/h</span>
        </div>
        <div class="stat-pill">
          <span class="stat-label">🏍 Xe máy</span>
          <span class="stat-value count-motor">0</span>
          <span class="stat-sub speed-motor">0 km/h</span>
        </div>
      </div>
    </div>
  `;

    return card;
}

/**
 * Cập nhật status badge với màu sắc tương ứng
 * @param {HTMLElement} badge
 * @param {string} status - "Thông thoáng" | "Đông đúc" | "Tắc nghẽn"
 */
function updateStatusBadge(badge, status) {
    badge.className = "status-badge";
    if (status === "Thông thoáng") {
        badge.classList.add("clear");
        badge.textContent = "✅ Thông thoáng";
    } else if (status === "Đông đúc") {
        badge.classList.add("busy");
        badge.textContent = "⚠️ Đông đúc";
    } else if (status === "Tắc nghẽn") {
        badge.classList.add("jammed");
        badge.textContent = "🔴 Tắc nghẽn";
    } else {
        badge.textContent = status || "—";
    }
}

/**
 * Format current time to HH:MM
 */
function fmtTime(date) {
    return (date || new Date()).toLocaleTimeString("vi-VN", {
        hour: "2-digit", minute: "2-digit",
    });
}