from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from authlib.integrations.starlette_client import OAuth
from app.core.config import settings
from fastapi import HTTPException, status

# ─────────────────────────────────────────────
# Google OAuth
# ─────────────────────────────────────────────

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


# ─────────────────────────────────────────────
# JWT
# ─────────────────────────────────────────────

def create_access_token(user_id: int, role: int) -> str:
    """Tạo JWT token chứa user_id và role.
    
    Args:
        user_id: ID của user trong DB
        role: 0 = admin, 1 = user thường
        
    Returns:
        JWT token string
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Giải mã JWT token và kiểm tra hợp lệ.
    
    Args:
        token: JWT token string từ request header
        
    Returns:
        dict chứa user_id và role
        
    Raises:
        HTTPException 401 nếu token không hợp lệ hoặc hết hạn
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: int = payload.get("user_id")
        role: int = payload.get("role")
        if user_id is None:
            raise credentials_exception
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise credentials_exception
