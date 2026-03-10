from pydantic import BaseModel


class ChatToolResponse(BaseModel):

    status: str
    road: str | None = None
    data: dict | None = None
    frame_url: str | None = None