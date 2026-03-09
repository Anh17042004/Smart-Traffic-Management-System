from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_current_user_ws
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.chat import repo as chat_repo
from app.modules.chat.schemas import ChatRequest, ChatResponse, ChatHistoryItem

router = APIRouter()

def _get_agent(request: Request):
    return request.app.state.chatbot

@router.post("/chat", response_model=ChatResponse, summary="Chat với AI (cần đăng nhập)")
async def chat(
    body: ChatRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = _get_agent(request)
    await chat_repo.save_message(db, current_user.id, "user", body.message)
    data = await agent.get_response(body.message, user_id=current_user.id)
    await chat_repo.save_message(db, current_user.id, "assistant", data["message"])
    return ChatResponse(**data)

@router.get("/chat/history", response_model=list[ChatHistoryItem], summary="Lịch sử chat")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    return await chat_repo.get_history(db, current_user.id, limit=limit)

@router.delete("/chat/history", summary="Xóa lịch sử chat")
async def clear_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await chat_repo.clear_history(db, current_user.id)
    return {"message": f"Đã xóa {count} tin nhắn."}

@router.websocket("/ws/chat")
async def ws_chat(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user_ws),
    db: AsyncSession = Depends(get_db),
):
    agent = websocket.app.state.chatbot
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "").strip()

            if not user_message:
                await websocket.send_json({"message": "Vui lòng nhập tin nhắn.", "image": None})
                continue

            await chat_repo.save_message(db, current_user.id, "user", user_message)
            response = await agent.get_response(user_message, user_id=current_user.id)
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
