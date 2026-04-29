import zoneinfo
from dataclasses import field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    TIMEZONE: zoneinfo.ZoneInfo = field(default_factory=lambda: zoneinfo.ZoneInfo("Asia/Seoul"))

    # Qdrant Vector DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION_MEDICAL: str = "medical_knowledge"
    QDRANT_COLLECTION_NUTRITION: str = "nutrition_knowledge"

    # RAG 동작 제어
    RAG_ENABLED: bool = True
    RAG_TOP_K: int = 3
    RAG_MIN_SCORE: float = 0.50
    # RAG 전후 비교 모드 (True이면 일반·RAG 응답 동시 반환, 개발·검증용)
    RAG_COMPARE: bool = False
