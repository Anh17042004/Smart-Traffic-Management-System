from pydantic import BaseModel
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None

class ChatResponse(BaseModel):
    message: str
    image: str | None = None

class ChatHistoryItem(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    model_config = {"from_attributes": True}
