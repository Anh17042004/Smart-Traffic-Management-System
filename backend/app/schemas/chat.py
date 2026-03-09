"""
schemas/chat.py
Pydantic schemas cho Chat API.
"""
from pydantic import BaseModel
from datetime import datetime


class ChatRequest(BaseModel):
    """Request gửi tin nhắn."""
    message: str
    session_id: int | None = None  # None = dùng session mặc định (user_id)


class ChatResponse(BaseModel):
    """Response từ AI Agent."""
    message: str
    image: str | None = None  # URL frame ảnh nếu agent gọi get_frame_road


class ChatHistoryItem(BaseModel):
    """Một tin nhắn trong lịch sử chat."""
    id: int
    role: str       # "user" hoặc "assistant"
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
