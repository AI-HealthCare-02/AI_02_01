from collections.abc import AsyncGenerator
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core import config

# quote_plus: 비밀번호에 @, :, / 등 특수문자가 포함된 경우 URL 인코딩 처리
# 예) "Password123@!" → "Password123%40%21" (URL에서 안전한 형태로 변환)
DATABASE_URL = f"mysql+asyncmy://{config.DB_USER}:{quote_plus(config.DB_PASSWORD)}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"

engine = create_async_engine(
    DATABASE_URL,
    pool_size=config.DB_CONNECTION_POOL_MAXSIZE,
    echo=False,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
