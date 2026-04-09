import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

# logging 기본 설정
# - level=INFO: INFO 이상의 로그(INFO, WARNING, ERROR)만 출력, DEBUG는 무시
# - format: 시간 | 로거이름 | 레벨 | 메시지 형식으로 출력
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

from app.apis.v1 import v1_routers
from app.core.config import Config
from app.core.redis import close_redis, init_redis
from app.database import Base
from app.db.databases import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시: 테이블 자동 생성 (개발용) + Redis 초기화
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_redis()
    yield
    # 서버 종료 시: Redis 해제 + 엔진 정리
    await close_redis()
    await engine.dispose()


app = FastAPI(
    default_response_class=ORJSONResponse,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS 미들웨어 추가 (프론트엔드 cross-origin 요청 허용)
config = Config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in config.CORS_ORIGINS.split(",")],
    allow_credentials=True,  # 쿠키(refresh_token) 포함 허용
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

app.include_router(v1_routers)
