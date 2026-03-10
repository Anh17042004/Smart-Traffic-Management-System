from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.database import get_db
from app.core.security import oauth, create_access_token
from app.services.auth import auth_services
from app.schemas.user import UserOut, TokenResponse
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/google")
async def login_google(request: Request):
    """Redirect sang trang đăng nhập Google.
    
    Frontend gọi: window.location.href = '/api/v1/auth/google'
    """
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Google gọi về đây sau khi user đăng nhập.
    
    Flow:
    1. Lấy token từ Google
    2. Lấy thông tin user (email, name, avatar)
    3. Upsert user vào DB
    4. Tạo JWT
    5. Redirect về frontend kèm token
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lỗi xác thực Google: {str(e)}"
        )

    # Lấy thông tin user từ Google
    user_info = token.get("userinfo")
    if not user_info:
        user_info = await oauth.google.userinfo(token=token)

    google_id = user_info["sub"]        # ID duy nhất từ Google
    email = user_info["email"]
    name = user_info.get("name", email)
    avatar_url = user_info.get("picture")

    # Upsert user vào DB
    user = await auth_services.upsert(db, google_id, email, name, avatar_url)

    # Tạo JWT token
    access_token = create_access_token(user_id=user.id, role=user.role)

    # Redirect về frontend kèm token trong query param
    frontend_url = f"{settings.URL_FRONTEND}/auth/callback.html?token={access_token}"
    return RedirectResponse(url=frontend_url)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    # """Trả về thông tin user hiện tại từ JWT token."
    return current_user


@router.post("/logout")
async def logout():
    # đăng xuất
    return {"message": "Đăng xuất thành công."}
