from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Tạo async engine kết nối PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,          # True để in SQL ra console khi debug
    pool_pre_ping=True,  # Tự động kiểm tra kết nối còn sống không
)

# Factory tạo session
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)



async def get_db() -> AsyncSession:
    """Dependency injection: inject DB session vào route handler.
    
    Dùng trong FastAPI:
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables():
    """Tạo tất cả bảng trong DB (dùng khi startup, thay thế Alembic trong dev nhanh)."""
    from app.models.base import Base
    # Import tất cả models để Base biết cần tạo bảng nào
    import app.models.user   # noqa
    import app.models.chat   # noqa

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
