from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User


async def get_by_google_id(db: AsyncSession, google_id: str) -> User | None:
    """Tìm user theo google_id."""
    result = await db.execute(select(User).where(User.google_id == google_id))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Tìm user theo id."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    google_id: str,
    email: str,
    name: str,
    avatar_url: str | None = None,
) -> User:
    """Tạo user mới. Lần đầu đăng nhập bằng Google."""
    user = User(
        google_id=google_id,
        email=email,
        name=name,
        avatar_url=avatar_url,
        role=1,  # mặc định là user thường
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def upsert(
    db: AsyncSession,
    google_id: str,
    email: str,
    name: str,
    avatar_url: str | None = None,
) -> User:
    """Tạo mới nếu chưa có, cập nhật name/avatar nếu đã có.
    
    Dùng trong callback sau khi Google trả về user info.
    """
    user = await get_by_google_id(db, google_id)
    if user:
        # Cập nhật thông tin mới nhất từ Google (avatar, tên có thể thay đổi)
        user.name = name
        user.avatar_url = avatar_url
        await db.commit()
        await db.refresh(user)
    else:
        user = await create(db, google_id, email, name, avatar_url)
    return user


async def update_role(db: AsyncSession, user_id: int, role: int) -> User | None:
    """Đổi role của user (admin dùng)."""
    user = await get_by_id(db, user_id)
    if not user:
        return None
    user.role = role
    await db.commit()
    await db.refresh(user)
    return user


async def get_all(db: AsyncSession) -> list[User]:
    """Lấy danh sách tất cả users (admin dùng)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


async def delete(db: AsyncSession, user_id: int) -> bool:
    """Xóa user theo id. Trả về True nếu xóa thành công."""
    user = await get_by_id(db, user_id)
    if not user:
        return False
    await db.delete(user)
    await db.commit()
    return True
