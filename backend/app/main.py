import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.apis.v1 import v1_routers
from app.core.config import Config
from app.core.redis import close_redis, init_redis
from app.database import Base
from app.db.databases import engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("api.access")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_redis()
    yield
    await close_redis()
    await engine.dispose()


app = FastAPI(
    default_response_class=ORJSONResponse,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # 헬스체크·정적 경로는 로깅 스킵
    if request.url.path in ("/health", "/favicon.ico"):
        return await call_next(request)

    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()

    # ── 요청 로깅
    logger.info(
        "[%s] REQUEST  %s %s | client=%s | content-type=%s",
        request_id,
        request.method,
        request.url.path,
        request.client.host if request.client else "-",
        request.headers.get("content-type", "-"),
    )

    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        logger.error(
            "[%s] UNHANDLED_ERROR %s %s | %.1fms | error=%s",
            request_id,
            request.method,
            request.url.path,
            elapsed,
            exc,
            exc_info=True,
        )
        raise

    elapsed = (time.perf_counter() - start) * 1000

    # 4xx/5xx는 WARNING/ERROR로 구분
    if response.status_code >= 500:
        log_fn = logger.error
    elif response.status_code >= 400:
        log_fn = logger.warning
    else:
        log_fn = logger.info

    log_fn(
        "[%s] RESPONSE %s %s | status=%d | %.1fms",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


# CORS 미들웨어 추가 (프론트엔드 cross-origin 요청 허용)
config = Config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in config.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_routers)


@app.get("/health", tags=["system"], summary="서버 상태 확인")
async def health_check():
    # 상태: true, 메시지: 정상 동작 안내
    return {
        "status": True,
        "message": "마이헬스버디 서버 정상 동작 합니다!"
    }
