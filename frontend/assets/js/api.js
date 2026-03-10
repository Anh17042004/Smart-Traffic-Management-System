/**
 * api.js — Fetch wrapper gửi Authorization: Bearer token từ localStorage
 */

const _API_BASE = CONFIG.API_BASE;

async function api(url, options = {}) {
    const token = getToken(); // từ auth.js

    // Merge headers
    options.headers = {
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {}),
    };

    const res = await fetch(_API_BASE + url, options);

    if (res.status === 401) {
        clearToken();
        goToLogin();
        throw new Error("Unauthorized");
    }

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Lỗi không xác định" }));
        throw new Error(err.detail || "API error");
    }

    if (res.status === 204) return null;
    return res.json();
}