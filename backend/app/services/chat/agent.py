from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings

from app.services.chat.tools import build_tools
from app.services.chat.prompt import prompt
from app.services.chat.chat_history import AsyncSQLAlchemyChatMessageHistory


class ChatBotAgent:

    def __init__(self, pool=None):

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.7,
        )

        self.tools = build_tools(pool) if pool else []

        agent = create_tool_calling_agent(
            self.llm,
            self.tools,
            prompt
        )

        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True
        )

    async def get_response(self, user_input, user_id, db):

        def get_session_history(session_id: str):

            return AsyncSQLAlchemyChatMessageHistory(
                db=db,
                user_id=int(session_id)
            )

        agent_with_history = RunnableWithMessageHistory(
            self.agent_executor,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )

        result = await agent_with_history.ainvoke(
            {"input": user_input},
            config={
                "configurable": {"session_id": str(user_id)}
            }
        )

        message = result["output"]

        if isinstance(message, list):
            message = "".join(
                part.get("text", "")
                for part in message
                if isinstance(part, dict)
            )

        return {
            "message": message,
            "image": None
        }