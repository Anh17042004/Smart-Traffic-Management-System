from typing import List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.chat_history import ChatHistory


def normalize_message(msg) -> str:

    if isinstance(msg, str):
        return msg

    if isinstance(msg, list):
        return "".join(
            part.get("text", "")
            for part in msg
            if isinstance(part, dict)
        )

    if isinstance(msg, dict):
        return msg.get("text", "")

    return str(msg)


class AsyncSQLAlchemyChatMessageHistory(BaseChatMessageHistory):

    def __init__(
        self,
        db: AsyncSession,
        user_id: int,
        max_messages: int = 12
    ):
        self.db = db
        self.user_id = user_id
        self.max_messages = max_messages

        self._messages: List[BaseMessage] = []
        self._loaded = False

    async def aget_messages(self) -> List[BaseMessage]:

        if not self._loaded:

            result = await self.db.execute(
                select(ChatHistory)
                .where(ChatHistory.user_id == self.user_id)
                .order_by(ChatHistory.id.desc())
                .limit(self.max_messages)
            )

            db_msgs = list(reversed(result.scalars().all()))

            messages: List[BaseMessage] = []

            for m in db_msgs:

                content = normalize_message(m.content)

                if m.role == "user":
                    messages.append(HumanMessage(content=content))

                elif m.role == "assistant":
                    messages.append(AIMessage(content=content))

                else:
                    messages.append(SystemMessage(content=content))

            self._messages = messages
            self._loaded = True

        return self._messages

    async def aadd_messages(self, messages: List[BaseMessage]) -> None:

        for msg in messages:

            role = "assistant"

            if isinstance(msg, HumanMessage):
                role = "user"

            elif isinstance(msg, AIMessage):
                role = "assistant"

            content = normalize_message(msg.content)

            db_msg = ChatHistory(
                user_id=self.user_id,
                role=role,
                content=content
            )

            self.db.add(db_msg)

            msg.content = content
            self._messages.append(msg)

        await self.db.commit()

    async def clear_db_history(self):

        await self.db.execute(
            delete(ChatHistory)
            .where(ChatHistory.user_id == self.user_id)
        )

        await self.db.commit()
    def clear(self) -> None:
        """
        Sync clear required by BaseChatMessageHistory.
        Không dùng vì hệ thống chạy async.
        """
        raise NotImplementedError("Use async aclear() instead")

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """
        Sync version required by BaseChatMessageHistory.
        Chúng ta không dùng vì hệ thống chạy async.
        """
        raise NotImplementedError("Use async aadd_messages() instead")