from typing import List

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_current_user, get_current_user_ws
from app.core.database import get_db
from app.models.user import User
from app.models.chat_history import ChatHistory

from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryItem

router: APIRouter = APIRouter()

def _get_agent(request: Request):
    """
    Lấy ChatBotAgent từ app.state
    """
    return request.app.state.chatbot


@router.post("/", response_model=ChatResponse,summary="Chat với AI (cần đăng nhập)")
async def chat(
    body: ChatRequest, 
    request: Request, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:

    agent = _get_agent(request)
    try:
        data = await agent.get_response(
            body.message,
            user_id=current_user.id,
            db=db
        )
    except Exception as e:

        error_msg: str = str(e)

        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            reply = "⚠️ Hệ thống AI đang quá tải (hết quota API). Vui lòng thử lại sau vài phút."
        else:
            reply = f"❌ Lỗi AI: {error_msg[:200]}" # pyre-ignore
        data = {"message": reply, "image": None}

    return ChatResponse(**data)


# Chat History
@router.get("/history", response_model=List[ChatHistoryItem], summary="Lịch sử chat")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):

    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.id.desc())
        .limit(limit)
    )

    rows = list(reversed(result.scalars().all()))

    return rows


@router.delete(
    "/history",
    summary="Xóa lịch sử chat"
)
async def clear_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(
        ChatHistory.__table__.delete()
        .where(ChatHistory.user_id == current_user.id)
    )
    await db.commit()
    return {"message": f"Đã xóa {result.rowcount} tin nhắn."}


# WebSocket Chat
@router.websocket("/ws/chat")
async def ws_chat(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user_ws),
    db: AsyncSession = Depends(get_db),
):

    agent = websocket.app.state.chatbot
    await websocket.accept()  # xác nhận kết nối ws
    try:
        while True:
            data = await websocket.receive_json()  # nhận message từ client
            user_message: str = data.get("message", "").strip()
            if not user_message:
                await websocket.send_json({
                    "message": "Vui lòng nhập tin nhắn.",
                    "image": None
                })
                continue
            response = await agent.get_response(
                user_message,
                user_id=current_user.id,
                db=db
            )
            await websocket.send_json(response)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS chat error: {e}")
        try:
            await websocket.send_json({
                "message": f"Lỗi: {str(e)}",
                "image": None
            })
        except Exception:
            pass
        await websocket.close()