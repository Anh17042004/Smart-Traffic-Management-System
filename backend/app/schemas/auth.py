from pydantic import BaseModel
from datetime import datetime


class UserOut(BaseModel):
    """Schema trả về thông tin user (không có thông tin nhạy cảm)."""
    id: int
    email: str
    name: str
    avatar_url: str | None
    role: int           # 0 = admin, 1 = user
    created_at: datetime

    model_config = {"from_attributes": True}  # Cho phép tạo từ ORM object


class TokenResponse(BaseModel):
    """Schema trả về sau khi đăng nhập thành công."""
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RoleUpdate(BaseModel):
    """Schema để admin đổi role của user."""
    role: int  # 0 = admin, 1 = user
