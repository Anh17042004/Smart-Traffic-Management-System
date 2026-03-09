const API_BASE_URL = 'http://localhost:8000/api/v1';

// Kiểm tra token
function getAuthToken() {
    return localStorage.getItem('access_token');
}

function requireAuth() {
    const token = getAuthToken();
    if (!token) {
        window.location.replace('index.html');
        return null;
    }
    return token;
}

// Cấu hình fetch mặc định có Auth Header
async function fetchWithAuth(endpoint, options = {}) {
    const token = requireAuth();
    if (!token) return null;

    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...(options.headers || {})
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // Token hết hạn hoặc sai
            logout();
            return null;
        }

        return response;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

function logout() {
    localStorage.removeItem('access_token');
    window.location.replace('index.html');
}

// Load thông tin user lên UI nếu có element #user-name, #user-avatar
async function loadUserInfo() {
    const res = await fetchWithAuth('/auth/me');
    if (res && res.ok) {
        const user = await res.json();
        const nameEl = document.getElementById('user-name');
        const avatarEl = document.getElementById('user-avatar');
        if (nameEl) nameEl.textContent = user.name;
        if (avatarEl && user.avatar_url) avatarEl.src = user.avatar_url;

        // Hiện tab admin nếu là admin
        if (user.role === 0) {
            const adminMenu = document.getElementById('nav-admin');
            if (adminMenu) adminMenu.classList.remove('d-none');
        }
    }
}
