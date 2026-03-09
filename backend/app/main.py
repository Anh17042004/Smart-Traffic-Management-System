from contextlib import asynccontextmanager
import os
import sys

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.core.config import settings
from app.core.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup và shutdown lifecycle của FastAPI app."""

    # ── Startup ──────────────────────────────────────
    print("📦 Khởi tạo database...")
    await create_tables()
    print("✅ Database sẵn sàng.")

    # Khởi động video processing workers
    print("🎥 Khởi động video processing workers...")
    from app.workers.video_processor import VideoProcessorPool
    app.state.processor = VideoProcessorPool()
    app.state.processor.run_multiprocessing()
    print(f"✅ Đang xử lý {len(app.state.processor.names)} tuyến đường.")

    # Khởi tạo AI Chatbot Agent (pass pool để tools truy cập data trực tiếp)
    print("🤖 Khởi tạo AI Chatbot Agent...")
    from app.ai.chatbot_agent import ChatBotAgent
    app.state.chatbot = ChatBotAgent(pool=app.state.processor)
    print("✅ AI Chatbot sẵn sàng.")

    yield  # ← Server chạy ở đây

    # ── Shutdown ─────────────────────────────────────
    print("🛑 Đang tắt workers...")
    if hasattr(app.state, "processor") and app.state.processor:
        app.state.processor.cleanup_processes()
    print("👋 Server đã tắt.")


# ─────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────

app = FastAPI(
    title="Smart Traffic Monitoring API",
    description="Hệ thống giám sát giao thông thông minh — Real-time · AI Chatbot · Google OAuth",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# SessionMiddleware PHẢI đặt trước CORSMiddleware
# authlib dùng session để lưu state OAuth2 (chống CSRF)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET_KEY,  # tái dụng JWT secret
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.URL_FRONTEND],  # chỉ cho phép frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────

from app.api.v1 import auth, traffic, chat, admin

app.include_router(auth.router,    prefix="/api/v1",        tags=["Authentication"])
app.include_router(traffic.router, prefix="/api/v1",        tags=["Traffic Monitoring"])
app.include_router(chat.router,    prefix="/api/v1",        tags=["AI Chatbot"])
app.include_router(admin.router,   prefix="/api/v1/admin",  tags=["Admin"])


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url=settings.URL_FRONTEND)
