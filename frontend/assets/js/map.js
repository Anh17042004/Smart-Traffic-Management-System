/**
 * map.js — Leaflet map với markers cho các tuyến đường
 * 
 * Tọa độ gần đúng các tuyến đường ở Hà Nội (có thể điều chỉnh lại).
 * Data traffic được fetch từ /roads/{name}/info mỗi 10 giây.
 */

// ── Tọa độ các tuyến đường ──
// Dùng tên video làm key (video1, video2, ...)
// Nếu backend trả về tên thật, update coords bên dưới
const ROAD_COORDS = {
  "video1": [21.0333, 105.8412],
  "video2": [21.0245, 105.8421],
  "Văn Quán": [20.9890, 105.7800],
  "Văn Phú": [20.9936, 105.7810],
  "Nguyễn Trãi": [20.9965, 105.7938],
  "Ngã Tư Sở": [21.0068, 105.8288],
  "Đường Láng": [21.0213, 105.8150],
};

const DEFAULT_COORD = [21.0285, 105.8542]; // Trung tâm Hà Nội

// ── Khởi tạo map ──
const map = L.map("map").setView([21.0145, 105.8100], 13);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors",
  maxZoom: 19,
}).addTo(map);

// ── Custom marker icon ──
function makeIcon(color) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="28" height="42">
    <path d="M12 0C5.37 0 0 5.37 0 12c0 7.5 12 24 12 24S24 19.5 24 12C24 5.37 18.63 0 12 0z" fill="${color}" stroke="white" stroke-width="1.5"/>
    <circle cx="12" cy="12" r="5" fill="white"/>
  </svg>`;
  return L.divIcon({
    html: svg,
    className: "",
    iconSize: [28, 42],
    iconAnchor: [14, 42],
    popupAnchor: [0, -42],
  });
}

const ICONS = {
  "Thông thoáng": makeIcon("#34d399"),
  "Đông đúc": makeIcon("#fbbf24"),
  "Tắc nghẽn": makeIcon("#f87171"),
  default: makeIcon("#38bdf8"),
};

const statusClass = {
  "Thông thoáng": "clear",
  "Đông đúc": "busy",
  "Tắc nghẽn": "jammed",
};

// ── Markers store ──
const markers = {};

function popupHtml(name, data) {
  const status = data.density_status || "—";
  const cls = statusClass[status] || "";
  return `
    <div class="popup-title">📍 ${name}</div>
    <div class="popup-row"><span>🚗 Ô tô</span><span class="popup-val">${data.count_car ?? 0} xe · ${data.speed_car ?? 0} km/h</span></div>
    <div class="popup-row"><span>🏍 Xe máy</span><span class="popup-val">${data.count_motor ?? 0} xe · ${data.speed_motor ?? 0} km/h</span></div>
    <div><span class="popup-status ${cls}">${status}</span></div>
  `;
}

async function loadRoads() {
  await loadNavbar();

  let roads = [];
  try {
    const data = await api("/roads");
    roads = data.road_names || [];
  } catch (e) {
    console.error("Không lấy được danh sách đường:", e);
    return;
  }

  for (const name of roads) {
    const coords = ROAD_COORDS[name] || DEFAULT_COORD;
    const marker = L.marker(coords, { icon: ICONS.default }).addTo(map);
    marker.bindPopup(`<div class="popup-title">📍 ${name}</div><p style="color:#64748b;font-size:12px">Đang tải dữ liệu...</p>`, { maxWidth: 260 });
    markers[name] = marker;
  }

  // Fetch và cập nhật popup mỗi 10 giây
  async function refreshAll() {
    for (const name of roads) {
      try {
        const data = await api(`/roads/${encodeURIComponent(name)}/info`);
        const marker = markers[name];
        if (!marker) continue;

        // Đổi màu icon theo status
        const iconKey = data.density_status || "default";
        marker.setIcon(ICONS[iconKey] || ICONS.default);
        marker.setPopupContent(popupHtml(name, data));
      } catch { }
    }
  }

  refreshAll();
  setInterval(refreshAll, 10000);
}

loadRoads();