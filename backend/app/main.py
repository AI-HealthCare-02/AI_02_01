from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.apis.v1 import v1_routers
from app.database import Base
from app.db.databases import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시: 테이블 자동 생성 (개발용)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 서버 종료 시: 엔진 정리
    await engine.dispose()


app = FastAPI(
    default_response_class=ORJSONResponse,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.include_router(v1_routers)
