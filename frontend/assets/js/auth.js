/**
 * auth.js — Auth helpers & shared navbar loader
 *
 * Flow:
 *   1. Sau Google OAuth callback, backend redirect về /dashboard/?token=<jwt>
 *   2. Frontend đọc token từ URL → lưu vào localStorage → xóa khỏi URL
 *   3. Mọi request REST gửi Authorization: Bearer <token>
 *   4. WebSocket gửi ?token=<jwt> query param
 */

const API_BASE = CONFIG.API_BASE;
const TOKEN_KEY = "traffic_token";

/**
 * Redirect về trang login (index.html ở root frontend).
 * Tính toán relative path dựa trên vị trí hiện tại.
 */
function goToLogin() {
    const depth = window.location.pathname.split("/").filter(Boolean).length;
    const prefix = depth > 0 ? "../".repeat(depth) : "./";
    window.location.href = prefix + "index.html";
}

// ── Token helpers ──────────────────────────────

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function saveToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

/**
 * Đọc token từ URL query param (sau Google OAuth redirect) và lưu vào localStorage.
 * Sau đó xóa token khỏi URL để không hiển thị trong browser.
 */
function captureTokenFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (token) {
        saveToken(token);
        // Xóa ?token=... khỏi URL bar (không reload trang)
        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
    }
}

/**
 * Kiểm tra token còn hợp lệ không bằng cách gọi /auth/me.
 * Nếu không hợp lệ → redirect về login.
 * @returns {Promise<Object|null>} user info
 */
async function requireAuth() {
    captureTokenFromUrl(); // Luôn gọi trước để bắt token mới sau redirect

    const token = getToken();
    if (!token) {
        goToLogin();
        return null;
    }

    try {
        const res = await fetch(`${API_BASE}/auth/me`, {
            headers: { "Authorization": `Bearer ${token}` },
        });

        if (!res.ok) {
            clearToken();
            goToLogin();
            return null;
        }

        return await res.json();
    } catch {
        goToLogin();
        return null;
    }
}

/**
 * Load và inject navbar.html, highlight active link, hiển thị user info.
 * @returns {Promise<Object|null>} user info
 */
async function loadNavbar() {
    // Capture token từ URL redirect trước (quan trọng trên dashboard page)
    captureTokenFromUrl();

    const container = document.getElementById("navbar-container");
    if (!container) return;

    // Inject navbar HTML
    const depth = window.location.pathname.split("/").filter(Boolean).length;
    const prefix = depth > 0 ? "../".repeat(depth) : "./";
    const navRes = await fetch(prefix + "components/navbar.html");
    container.innerHTML = await navRes.text();

    // Highlight active link
    const path = window.location.pathname;
    const links = {
        "nav-dashboard": "/dashboard",
        "nav-map": "/map",
        "nav-chat": "/chat",
    };
    for (const [id, href] of Object.entries(links)) {
        const el = document.getElementById(id);
        if (el && path.startsWith(href)) el.classList.add("active");
    }

    // Logout button
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", async () => {
            const token = getToken();
            await fetch(`${API_BASE}/auth/logout`, {
                method: "POST",
                headers: token ? { "Authorization": `Bearer ${token}` } : {},
            }).catch(() => { });
            clearToken();
            goToLogin();
        });
    }

    // Lấy user info
    const user = await requireAuth();
    if (!user) return null;

    const avatarEl = document.getElementById("navAvatar");
    const nameEl = document.getElementById("navName");

    if (nameEl) nameEl.textContent = user.name || user.email;

    if (avatarEl) {
        if (user.avatar_url) {
            avatarEl.innerHTML = `<img src="${user.avatar_url}" alt="${user.name}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">`;
        } else {
            avatarEl.textContent = (user.name || "?")[0].toUpperCase();
        }
    }

    return user;
}