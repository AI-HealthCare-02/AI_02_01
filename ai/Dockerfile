FROM python:3.13-slim

WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 1. uv 설치 (공식 이미지에서 복사해오는 가장 깔끔한 방법)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 2. 의존성 패키지 관리 파일을 컨테이너 내부에 복사합니다.
COPY pyproject.toml uv.lock ./

# 3. pyproject.toml에 명시된 의존성 패키지 중에서 'ai' 그룹만 설치합니다.
RUN uv sync --group ai --no-dev --frozen

# 4. 로컬 소스 코드를 컨테이너 내부로 복사합니다.
COPY ./ai ./ai

# 5. 모델 파일 경로 환경변수 설정 (Docker 내 경로)
ENV ML1_MODEL_PATH=/app/ai/models/xgboost_model.pkl
ENV ML1_SCALER_PATH=/app/ai/models/scaler.pkl

# 6. Celery Worker 실행
CMD ["uv", "run", "celery", "-A", "ai.celery_app", "worker", "--loglevel=info"]
