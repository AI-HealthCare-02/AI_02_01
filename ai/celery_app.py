"""
Celery 통합 설정 파일

역할: Vision + ML1 Worker가 공통으로 사용하는 Celery 인스턴스

Redis DB 할당:
  DB 0 - Celery Broker  : task 대기열 (FastAPI → Redis → Worker)
  DB 1 - Celery Backend : task 완료 결과 저장 (Worker → Redis → FastAPI)
  DB 2 - ML1 Cache      : 분석 결과 캐시 (24시간 TTL)
"""

import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# Redis 연결 (DB 분리)
# ──────────────────────────────────────────────
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://localhost:6379/1")

# ──────────────────────────────────────────────
# Celery 인스턴스 생성
# ──────────────────────────────────────────────
celery_app = Celery(
    "ai_worker",
    broker=BROKER_URL,    # DB 0: task 대기열
    backend=BACKEND_URL,  # DB 1: task 완료 결과 저장
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
