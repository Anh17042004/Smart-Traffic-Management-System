"""
api/v1/chat.py
Refactored từ api_chatbot.py cũ.

Endpoints:
  POST /chat              → gửi tin nhắn, nhận response (yêu cầu auth)
  GET  /chat/history      → lịch sử chat từ DB
  DELETE /chat/history    → xóa lịch sử
  WS   /ws/chat           → WebSocket chat realtime
"""
from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, get_current_user_ws
from app.core.database import get_db
from app.models.user import User
from app.repositories import chat_repo
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryItem

router = APIRouter()


def _get_agent(request: Request):
    """Lấy ChatBotAgent từ app.state (được khởi tạo trong lifespan)."""
    return request.app.state.chatbot


# ─────────────────────────────────────────────
# REST Endpoints
# ─────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse, summary="Chat với AI (cần đăng nhập)")
async def chat(
    body: ChatRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Gửi tin nhắn tới AI Agent và nhận phản hồi.

    Context chat được giữ theo user_id (InMemorySaver trong RAM).
    Tin nhắn và phản hồi được lưu vào DB (chat_history).
    """
    agent = _get_agent(request)

    # Lưu tin nhắn của user
    await chat_repo.save_message(db, current_user.id, "user", body.message)

    # Gọi agent
    data = await agent.get_response(body.message, user_id=current_user.id)

    # Lưu phản hồi của assistant
    await chat_repo.save_message(db, current_user.id, "assistant", data["message"])

    return ChatResponse(**data)


@router.get("/chat/history", response_model=list[ChatHistoryItem], summary="Lịch sử chat")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    """Trả về lịch sử chat gần nhất của user từ DB."""
    return await chat_repo.get_history(db, current_user.id, limit=limit)


@router.delete("/chat/history", summary="Xóa lịch sử chat")
async def clear_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Xóa toàn bộ lịch sử chat của user trong DB."""
    count = await chat_repo.clear_history(db, current_user.id)
    return {"message": f"Đã xóa {count} tin nhắn."}


# ─────────────────────────────────────────────
# WebSocket
# ─────────────────────────────────────────────

@router.websocket("/ws/chat")
async def ws_chat(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user_ws),
    db: AsyncSession = Depends(get_db),
):
    """WebSocket chat realtime.

    Client gửi:  {"message": "Đường Láng thế nào?"}
    Server trả:  {"message": "...", "image": "url hoặc null"}

    Auth: ws://localhost:8000/api/v1/ws/chat?token=<jwt>
    """
    agent = websocket.app.state.chatbot
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "").strip()

            if not user_message:
                await websocket.send_json({"message": "Vui lòng nhập tin nhắn.", "image": None})
                continue

            # Lưu tin nhắn user
            await chat_repo.save_message(db, current_user.id, "user", user_message)

            # Gọi agent
            response = await agent.get_response(user_message, user_id=current_user.id)

            # Lưu phản hồi
            await chat_repo.save_message(db, current_user.id, "assistant", response["message"])

            await websocket.send_json(response)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS chat error: {e}")
        try:
            await websocket.send_json({"message": f"Lỗi: {str(e)}", "image": None})
        except:
            pass
        await websocket.close()
