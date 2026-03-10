import json
from typing import Annotated

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver

from app.core.config import settings
from app.modules.chat.schemas import ChatResponse

# ─────────────────────────────────────────────
# System Prompt
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """Bạn là một trợ lý AI chuyên tư vấn giao thông bằng TIẾNG VIỆT.

MỤC TIÊU CHÍNH:
- Hiểu rõ ý định người dùng, trả lời ngắn gọn, chính xác và có cấu trúc.
- Khi được hỏi về tuyến đường, BẮT BUỘC gọi tool `get_info_road` để lấy dữ liệu thực.
- Nếu người dùng yêu cầu ảnh, gọi `get_frame_road` để trả URL ảnh.
- Nếu cần biết danh sách đường, gọi `get_roads`.

ĐỊNH DẠNG TRẢ LỜI (LUÔN BẰNG TIẾNG VIỆT):
1. Tóm tắt ngắn (1 câu)
2. Với mỗi tuyến đường:
   - Số lượng ô tô: X | Vận tốc TB: Y km/h
   - Số lượng xe máy: A | Vận tốc TB: B km/h
   - Trạng thái: Thông thoáng / Đông đúc / Tắc nghẽn
3. Khuyến nghị (2-3 gợi ý)

HƯỚNG DẪN HÀNH VI:
- Nếu người dùng không nói rõ tuyến đường, HỎI lại.
- Luôn trả lời bằng tiếng Việt, giọng chuyên nghiệp và thân thiện.
- Nếu không có dữ liệu, nói rõ: "Không có dữ liệu cho tuyến X".
"""


def build_tools(pool) -> list:
    """Tạo LangChain tools với VideoProcessorPool được inject vào closure."""

    @tool
    def get_roads() -> str:
        """Lấy danh sách các tuyến đường đang được giám sát."""
        return json.dumps({"roads": pool.get_names()}, ensure_ascii=False)

    @tool
    def get_info_road(road_name: Annotated[str, "Tên tuyến đường, ví dụ: Đường Láng"]) -> str:
        """Lấy thông tin phương tiện thời gian thực của tuyến đường.
        Trả về JSON gồm count_car, count_motor, speed_car, speed_motor, density_status.
        """
        data = pool.get_info_road(road_name)
        if not data:
            return json.dumps(
                {"error": f"Không có dữ liệu cho '{road_name}'"}, ensure_ascii=False
            )
        return json.dumps(data, ensure_ascii=False)

    @tool
    def get_frame_road(road_name: Annotated[str, "Tên tuyến đường"]) -> str:
        """Lấy URL ảnh frame hiện tại của tuyến đường để hiển thị cho người dùng.
        Trả về URL endpoint: /api/v1/roads/{road_name}/frame
        """
        return f"/api/v1/roads/{road_name}/frame"

    return [get_roads, get_info_road, get_frame_road]


class ChatBotAgent:
    def __init__(self, pool=None):
        """
        Args:
            pool: VideoProcessorPool instance. Tools sẽ gọi trực tiếp qua pool.
        """
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.7,
        )
        self.checkpointer = InMemorySaver()
        tools = build_tools(pool) if pool else []

        # langchain 1.x API
        self.agent = create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            response_format=ToolStrategy(ChatResponse),  # structured output
            checkpointer=self.checkpointer,              # per-user memory
        )

    async def get_response(self, user_input: str, user_id: int) -> dict:
        config = {"configurable": {"thread_id": str(user_id)}}
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
        )
        return result["structured_response"].model_dump()
