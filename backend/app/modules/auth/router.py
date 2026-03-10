from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import oauth, create_access_token
from app.modules.auth import repo as user_repo
from app.modules.auth.schemas import UserOut, TokenResponse
from app.modules.auth.models import User
from app.core.dependencies import get_current_user

router = APIRouter()


@router.get("/auth/google")
async def login_google(request: Request):
    """Redirect sang trang đăng nhập Google."""
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Google gọi về đây sau khi user đăng nhập."""
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lỗi xác thực Google: {str(e)}"
        )

    user_info = token.get("userinfo")
    if not user_info:
        user_info = await oauth.google.userinfo(token=token)

    google_id = user_info["sub"]
    email = user_info["email"]
    name = user_info.get("name", email)
    avatar_url = user_info.get("picture")

    user = await user_repo.upsert(db, google_id, email, name, avatar_url)

    access_token = create_access_token(user_id=user.id, role=user.role)

    # Redirect về frontend kèm token trong URL param.
    # Frontend JS sẽ đọc ?token=... và lưu vào localStorage,
    # sau đó gửi qua Authorization: Bearer header cho mọi request.
    # Cách này hoạt động tốt với cross-origin (5500 → 8000) và WebSocket.
    response = RedirectResponse(
        url=f"{settings.URL_FRONTEND}/dashboard/?token={access_token}"
    )

    return response


@router.get("/auth/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Trả về thông tin user hiện tại từ JWT token."""
    return current_user


@router.post("/auth/logout")
async def logout():
    """Đăng xuất."""
    return {"message": "Đăng xuất thành công. Vui lòng xóa token phía client."}
