"""
로컬 테스트용 Access Token 발급 스크립트.

사용법:
    uv run python scripts/gen_token.py --user-id 1
    uv run python scripts/gen_token.py --user-id 1 --env envs/.local.env

주의:
    - 서버와 동일한 SECRET_KEY를 사용해야 토큰 검증이 통과된다.
    - .env 또는 envs/.local.env 파일의 SECRET_KEY가 서버와 일치하는지 확인한다.
    - 이 스크립트는 로컬 개발/테스트 전용으로, 프로덕션 환경에서 사용 금지.
"""

import argparse
import os
import sys
from pathlib import Path

# 프로젝트 루트 기준으로 backend/ 를 파이썬 경로에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


def load_env(env_file: str) -> None:
    """지정된 env 파일을 환경변수로 로드."""
    env_path = PROJECT_ROOT / env_file
    if not env_path.exists():
        print(f"[경고] env 파일을 찾을 수 없음: {env_path}")
        print("  → 기본 설정(config.py default)으로 진행합니다.")
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

    print(f"[정보] env 파일 로드 완료: {env_path}")


def generate_token(user_id: int) -> str:
    """주어진 user_id로 AccessToken을 생성하고 문자열로 반환."""
    # env 로드 이후에 import (SECRET_KEY 등이 먼저 환경변수에 설정되어야 함)
    from app.utils.jwt.tokens import AccessToken
    from app.core import config as cfg

    class _MockUser:
        """AccessToken.for_user()가 필요로 하는 최소 User 객체."""
        def __init__(self, uid: int):
            self.id = uid

    token = AccessToken.for_user(_MockUser(user_id))
    token_str = str(token)

    print(f"\n{'=' * 60}")
    print(f"  User ID    : {user_id}")
    print(f"  Token Type : access")
    print(f"  Algorithm  : {cfg.JWT_ALGORITHM}")
    print(f"  Expire     : {cfg.ACCESS_TOKEN_EXPIRE_MINUTES // 60 // 24}일 후 만료")
    print(f"{'=' * 60}")
    print(f"\n[Access Token]\n{token_str}\n")
    print("[사용 방법] Swagger UI → Authorize → Bearer {위 토큰 붙여넣기}")
    print("[사용 방법] curl -H 'Authorization: Bearer {위 토큰}' http://localhost:8000/...\n")

    return token_str


def main() -> None:
    parser = argparse.ArgumentParser(description="로컬 테스트용 Access Token 발급 스크립트")
    parser.add_argument("--user-id", type=int, required=True, help="토큰을 발급할 사용자 ID (users.id)")
    parser.add_argument(
        "--env",
        type=str,
        default="envs/.local.env",
        help="env 파일 경로 (프로젝트 루트 기준, 기본값: envs/.local.env)",
    )
    args = parser.parse_args()

    load_env(args.env)
    generate_token(args.user_id)


if __name__ == "__main__":
    main()
