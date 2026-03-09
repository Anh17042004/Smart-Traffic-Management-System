document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth()) return;

    // Check role, nếu không phải admin (hoặc fetch lỗi 403) sẽ báo lỗi
    await loadUserInfo();

    // Load data song song
    Promise.all([
        loadSystemMetrics(),
        loadUsers()
    ]);
});

async function loadSystemMetrics() {
    try {
        const res = await fetchWithAuth('/admin/system');
        if (res && res.ok) {
            const data = await res.json();
            document.getElementById('metric-cpu').textContent = `${data.cpu.percent}%`;
            document.getElementById('metric-ram').textContent = `${data.memory.used_gb} GB / ${data.memory.total_gb} GB`;
            document.getElementById('metric-disk').textContent = `${data.disk.percent}%`;
        }
    } catch (e) {
        console.error("System Metrics error", e);
    }
}

async function loadUsers() {
    try {
        const res = await fetchWithAuth('/admin/users');
        if (res && res.ok) {
            const users = await res.json();
            const tbody = document.getElementById('users-tbody');
            tbody.innerHTML = '';

            users.forEach(u => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${u.id}</td>
                    <td><img src="${u.avatar_url || 'https://ui-avatars.com/api/?name=User'}" width="30" class="rounded-circle"></td>
                    <td>${u.email}</td>
                    <td>${u.name}</td>
                    <td>
                        <select class="form-select form-select-sm bg-dark text-white border-secondary select-role" data-id="${u.id}">
                            <option value="0" ${u.role === 0 ? 'selected' : ''}>Admin</option>
                            <option value="1" ${u.role === 1 ? 'selected' : ''}>User</option>
                        </select>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger btn-delete" data-id="${u.id}">Xóa</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });

            // Gắn event listener
            document.querySelectorAll('.select-role').forEach(select => {
                select.addEventListener('change', async (e) => {
                    const id = e.target.dataset.id;
                    const newRole = parseInt(e.target.value);
                    await updateRole(id, newRole);
                });
            });

            document.querySelectorAll('.btn-delete').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const id = e.target.dataset.id;
                    if (confirm('Bạn có chắc muốn xóa user này?')) {
                        await deleteUser(id);
                    }
                });
            });
        }
    } catch (e) {
        console.error("Users error", e);
        document.getElementById('users-tbody').innerHTML = '<tr><td colspan="6" class="text-danger text-center">Lỗi tải dữ liệu. Cần quyền Admin.</td></tr>';
    }
}

async function updateRole(id, role) {
    try {
        const res = await fetchWithAuth(`/admin/users/${id}/role`, {
            method: 'PATCH',
            body: JSON.stringify({ role })
        });
        if (res && res.ok) alert('Cập nhật quyền thành công!');
        else alert('Có lỗi xảy ra, có thể bạn không được phép đổi quyền chính mình.');
    } catch (e) {
        alert('Lỗi cập nhật. Xem console.');
    }
}

async function deleteUser(id) {
    try {
        const res = await fetchWithAuth(`/admin/users/${id}`, { method: 'DELETE' });
        if (res && res.ok) {
            alert('Xóa thành công!');
            loadUsers(); // reload bảng
        } else {
            alert('Có lỗi xảy ra hoặc không thể xóa chính mình.');
        }
    } catch (e) {
        alert('Lỗi xóa. Xem console.');
    }
}
