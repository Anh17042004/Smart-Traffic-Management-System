from langchain_core.prompts import ChatPromptTemplate

SYSTEM_PROMPT = """
Bạn là trợ lý AI tư vấn giao thông tại Việt Nam.
Luôn trả lời bằng tiếng Việt.

Chỉ sử dụng dữ liệu từ tools khi cần thông tin giao thông hoặc camera.
Không tự tạo dữ liệu.

Nếu tool trả:
- status = success → dùng dữ liệu để trả lời
- status = not_found → thông báo không có dữ liệu
- status = error → thông báo lỗi hệ thống
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])