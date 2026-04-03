"""
Celery 설정 파일

역할: Celery Worker가 Redis를 브로커(주문 대기열)로 사용하도록 설정
위치: 현재 ai/vision/ 안에 임시 배치 → 나중에 ai/ 루트로 이동 권장

Docker 네트워크(ws) 안에서 컨테이너 이름이 곧 주소:
  redis://redis:6379/0
  ~~~~~~~~ ~~~~~ ~~~~ ~
  프로토콜  컨테이너  포트  DB번호
"""

import os
from celery import Celery
from dotenv import load_dotenv    # ← 추가

load_dotenv()                     # ← 추가 (.env 파일 읽어서 환경변수에 등록)
# ──────────────────────────────────────────────
# Redis 연결
# ──────────────────────────────────────────────
# .env에 REDIS_URL이 있으면 사용, 없으면 docker-compose 기본값
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ──────────────────────────────────────────────
# Celery 인스턴스 생성
# ──────────────────────────────────────────────
celery_app = Celery(
    "ai_worker",          # 앱 이름 (로그에 표시)
    broker=REDIS_URL,     # 주문서 꽂이 (작업 대기열)
    backend=REDIS_URL,    # 결과 저장소 (FastAPI가 조회)
)

# ──────────────────────────────────────────────
# 상세 설정
# ──────────────────────────────────────────────
celery_app.conf.update(
    # Celery가 작업(task)을 찾을 모듈 경로
    # → tasks.py 안의 @celery_app.task 함수들을 자동 등록
    include=["ai.vision.tasks"],

    # 결과 유효시간: 1시간 후 자동 삭제
    result_expires=3600,

    # 직렬화 방식: JSON (사람이 읽을 수 있음)
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # 시간대
    timezone="Asia/Seoul",
    enable_utc=False,

    # Worker가 한 번에 가져오는 작업 수
    # Vision API는 응답이 느리니까 1개씩 처리
    worker_prefetch_multiplier=1,

    # 작업 타임아웃: 60초 (GPT API 응답 대기)
    task_time_limit=60,

    # 소프트 타임아웃: 50초 (50초 지나면 경고, 60초에 강제 종료)
    task_soft_time_limit=50,
)
