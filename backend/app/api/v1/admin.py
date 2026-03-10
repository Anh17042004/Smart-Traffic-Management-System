import psutil
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_admin
from app.core.database import get_db
from app.models.user import User
from app.services.auth import auth_services
from app.schemas.user import RoleUpdate, UserOut

router = APIRouter()

# ─────────────────────────────────────────────
# User Management
# ─────────────────────────────────────────────

@router.get("/users", response_model=list[UserOut], summary="Danh sách tất cả users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin xem toàn bộ danh sách users."""
    return await auth_services.get_all(db)


@router.get("/users/{user_id}", response_model=UserOut, summary="Chi tiết user")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin xem thông tin 1 user theo ID."""
    user = await auth_services.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user.")
    return user


@router.patch("/users/{user_id}/role", response_model=UserOut, summary="Đổi role user")
async def update_role(
    user_id: int,
    body: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Admin thay đổi role của user."""
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Không thể tự thay đổi role của chính mình.")

    user = await auth_services.update_role(db, user_id, body.role)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user.")
    return user


@router.delete("/users/{user_id}", summary="Xóa user")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Admin xóa user khỏi hệ thống."""
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Không thể tự xóa tài khoản của chính mình.")

    deleted = await auth_services.delete(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Không tìm thấy user.")
    return {"message": f"Đã xóa user {user_id}."}


# ─────────────────────────────────────────────
# System Info
# ─────────────────────────────────────────────

@router.get("/system", summary="Thông tin hệ thống server")
async def system_info(_: User = Depends(require_admin)):
    """Trả về CPU, RAM, Disk usage của server."""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "cpu": {
            "percent": cpu,
            "count": psutil.cpu_count(),
        },
        "memory": {
            "total_gb": round(mem.total / 1e9, 2),
            "used_gb": round(mem.used / 1e9, 2),
            "percent": mem.percent,
        },
        "disk": {
            "total_gb": round(disk.total / 1e9, 2),
            "used_gb": round(disk.used / 1e9, 2),
            "percent": disk.percent,
        },
    }


# ─────────────────────────────────────────────
# Roads Overview (admin view)
# ─────────────────────────────────────────────

@router.get("/roads", summary="Tổng quan tất cả tuyến đường")
async def admin_roads(
    request: Request,
    _: User = Depends(require_admin),
):
    """Admin xem danh sách tuyến đường + metrics hiện tại."""
    pool = request.app.state.processor
    names = pool.get_names()

    roads = []
    for name in names:
        data = pool.get_info_road(name)
        roads.append({
            "name": name,
            "active": data is not None,
            "data": dict(data) if data else {},
        })

    return {
        "total_roads": len(roads),
        "roads": roads,
    }
