"""
repositories/chat_repo.py
CRUD cho bảng chat_history.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.chat import ChatHistory


async def save_message(
    db: AsyncSession,
    user_id: int,
    role: str,
    content: str,
) -> ChatHistory:
    """Lưu 1 tin nhắn (user hoặc assistant) vào DB."""
    msg = ChatHistory(user_id=user_id, role=role, content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_history(
    db: AsyncSession,
    user_id: int,
    limit: int = 50,
) -> list[ChatHistory]:
    """Lấy lịch sử chat gần nhất của user (mới nhất trước)."""
    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))


async def clear_history(db: AsyncSession, user_id: int) -> int:
    """Xóa toàn bộ lịch sử chat của user. Trả về số dòng bị xóa."""
    result = await db.execute(
        delete(ChatHistory).where(ChatHistory.user_id == user_id)
    )
    await db.commit()
    return result.rowcount
