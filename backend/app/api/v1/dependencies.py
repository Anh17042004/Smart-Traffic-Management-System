from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from sqlalchemy import select

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: Xác thực JWT token và trả về User hiện tại.
    
    Dùng trong route:
        async def my_route(user: User = Depends(get_current_user)):
            ...
    
    Raises:
        401 nếu không có token hoặc token không hợp lệ
        404 nếu user không tồn tại trong DB
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập. Vui lòng đăng nhập bằng Google.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    user_id = payload["user_id"]

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài khoản.",
        )
    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency: Chỉ cho phép admin truy cập.
    
    Dùng trong route admin:
        async def admin_route(user: User = Depends(require_admin)):
            ...
    
    Raises:
        403 nếu user không phải admin (role != 0)
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập trang này.",
        )
    return current_user
