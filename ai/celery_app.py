"""
Celery 통합 설정 파일

역할: Vision + ML1 Worker가 공통으로 사용하는 Celery 인스턴스
브로커: Redis (Docker 네트워크 내 redis://redis:6379/0)
"""

import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# Redis 연결
# ──────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ──────────────────────────────────────────────
# Celery 인스턴스 생성
# ──────────────────────────────────────────────
celery_app = Celery(
    "ai_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# ──────────────────────────────────────────────
# 상세 설정
# ──────────────────────────────────────────────
celery_app.conf.update(
    # Vision + ML1 task 모듈 자동 등록
    include=[
        "ai.vision.tasks",
        "ai.workers.tasks",
    ],
    # 결과 유효시간: 1시간 후 자동 삭제
    result_expires=3600,
    # 직렬화 방식: JSON
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # 시간대
    timezone="Asia/Seoul",
    enable_utc=False,
    # Worker가 한 번에 가져오는 작업 수
    worker_prefetch_multiplier=1,
    # 작업 타임아웃: 120초 (ML1은 OpenAI API 호출 포함)
    task_time_limit=300,
    # 소프트 타임아웃: 110초
    task_soft_time_limit=280,
)
