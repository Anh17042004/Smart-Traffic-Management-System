import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.core.config import settings
from app.core.database import create_tables


os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):

    # ── Database ──────────────────────────────
    logger.info("📦 Initializing database...")
    await create_tables()
    logger.info("✅ Database ready.")

    # ── Video processors ──────────────────────
    logger.info("🎥 Starting video processing workers...")

    from app.workers.video_processor import VideoProcessorPool

    processor = VideoProcessorPool()
    processor.run_multiprocessing()

    app.state.processor = processor

    logger.info(f"✅ Processing {len(processor.names)} roads.")

    # ── Chatbot agent ─────────────────────────
    logger.info("🤖 Initializing AI Chatbot Agent...")

    from app.services.chat.agent import ChatBotAgent

    chatbot = ChatBotAgent(pool=processor)

    app.state.chatbot = chatbot

    logger.info("✅ Chatbot ready.")

    yield

    #Shutdown 
    logger.info("🛑 Shutting down workers...")

    if hasattr(app.state, "processor"):
        app.state.processor.cleanup_processes()

    logger.info("👋 Server stopped.")


# FastAPI App
app = FastAPI(
    title="Smart Traffic Monitoring API",
    description="Real-time traffic monitoring + AI Chatbot",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# OAuth session (Authlib cần)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET_KEY,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.URL_FRONTEND],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.auth import router as auth_router
from app.api.v1.traffic import router as traffic_router
from app.api.v1.chat import router as chat_router
from app.api.v1.admin import router as admin_router


app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(traffic_router, prefix="/api/v1/traffic", tags=["Traffic"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chatbot"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])

# Root redirect
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url=settings.URL_FRONTEND)