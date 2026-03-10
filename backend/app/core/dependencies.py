from fastapi import Depends, HTTPException, Query, WebSocket, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: Xác thực JWT token và trả về User hiện tại."""
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
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản.")
    return user


async def get_current_user_ws(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token — gửi qua ?token=<jwt>"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency dành cho WebSocket — auth qua query param ?token=..."""
    try:
        payload = decode_token(token)
        user_id = payload["user_id"]
    except Exception:
        await websocket.close(code=4001)
        raise HTTPException(status_code=401, detail="Token không hợp lệ.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        await websocket.close(code=4004)
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản.")
    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency: Chỉ cho phép admin truy cập."""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập trang này.",
        )
    return current_user
