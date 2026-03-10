/**
 * config.js — Cấu hình tập trung cho frontend
 *
 * Tất cả URL backend đều đọc từ đây.
 * Khi deploy production, chỉ cần đổi giá trị trong file này.
 */

const CONFIG = Object.freeze({
    // Base URL cho REST API (không có trailing slash)
    API_BASE: "http://localhost:8000/api/v1",

    // Base URL cho WebSocket (ws:// hoặc wss://)
    WS_BASE: "ws://localhost:8000/api/v1",

    // URL backend gốc (dùng cho OAuth redirect, v.v.)
    BACKEND_URL: "http://localhost:8000",
});
