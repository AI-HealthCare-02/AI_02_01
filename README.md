# MyHealthBuddy (마이헬스버디)

> 건강검진 수치 입력 → 심혈관 위험도 예측 → 위험 요인별 챌린지 추천

---

## 서비스 소개

건강검진 수치를 입력하면 XGBoost 모델이 심혈관 위험도(%)와 심혈관 나이를 예측하고, 주요 위험 요인에 맞는 생활습관 챌린지를 자동으로 추천하는 웹 서비스입니다. 매일 챌린지를 수행하면 위험도가 재예측되어 건강 개선 효과를 직접 확인할 수 있습니다.

---

## 저장소 구성

| 역할 | 저장소 |
|---|---|
| Backend / AI | https://github.com/AI-HealthCare-02/AI_02_01 (현재 저장소) |
| Frontend | https://github.com/OZ-DailyCare-Challenge/frontend |

---

## 팀원

| 이름 | 역할 |
|---|---|
| 조영현 | 백엔드 개발 및 서버 배포, 성능 테스트 |
| 이형석 | Vision AI, 건강검진 OCR, 백엔드 보조 |
| 이승희 | AI 모델링, 백엔드 API 설계, 프론트엔드 보조 |
| 박소윤 | 프론트엔드 개발 및 UI/UX 구조화, 성능 테스트 |

---

## 기술 스택

**Frontend**
- Next.js 16, React 19, TypeScript, Tailwind CSS 4
- Zustand (상태 관리), Framer Motion (애니메이션), Three.js (3D)
- Axios, Lucide React, Google OAuth 2.0
- 배포: Vercel

**Backend**
- FastAPI, SQLAlchemy 2.0 (async), MySQL 8.0
- Google OAuth 2.0 + JWT
- Redis (Pub/Sub, Stream), Celery (비동기 태스크)
- Nginx (리버스 프록시)
- 패키지 관리: uv

**AI / Data**
- XGBoost, SHAP, scikit-learn (심혈관 위험도 예측)
- OpenAI ChatGPT (건강 코멘트, Vision 기반 식단/운동 인증)
- Langfuse (LLM 사용량 및 비용 추적)
- RAG (Qdrant 벡터 DB + LangChain)
- Pandas, NumPy

**Infra**
- AWS EC2, Docker Compose, GitHub Actions (CI/CD)

---

## 시스템 아키텍처

![시스템 아키텍처](docs/architecture.png)

---

## 프로젝트 문서

| 문서 | 링크 |
|---|---|
| 요구사항 정의서 | [docs/requirements.md](docs/requirements.md) |
| ERD | [docs/erd.md](docs/erd.md) |
| API 명세서 | [Notion](https://www.notion.so/API-330e5d4a0bac800d9bebfb05d9209c3e) |
| 와이어프레임 | Figma (추후 링크 추가) |

---

## 프로젝트 구조

```
AI_02_01/                  # Backend + AI (현재 저장소)
├── backend/
│   └── app/
│       ├── apis/v1/       # 라우터 (HTTP 엔드포인트)
│       ├── services/      # 비즈니스 로직
│       ├── repositories/  # DB CRUD (SQLAlchemy)
│       ├── models/        # SQLAlchemy 모델
│       ├── dtos/          # Pydantic 요청/응답 DTO
│       └── dependencies/  # FastAPI Depends (인증 등)
├── ai/
│   ├── models/            # 학습된 XGBoost 모델 파일
│   ├── rag/               # RAG 파이프라인 (Qdrant)
│   ├── vision/            # GPT Vision 기반 이미지 분석
│   └── tasks/             # Celery 비동기 태스크
├── data/                  # 공통 데이터
├── docs/                  # 프로젝트 문서
└── envs/                  # 환경변수 예시
```

---

## 브랜치 전략

```
main
└── develop
    ├── feat/frontend
    ├── feat/backend
    ├── feat/ai
    └── feat/data
```

- `feat/*` → `develop` : PR + 리뷰어 1명 승인
- `develop` → `main` : PR + 리뷰어 2명 승인

---

## 커밋 규칙

| 타입 | 설명 |
|---|---|
| feat | 새로운 기능 추가 |
| fix | 버그 수정 |
| docs | 문서 수정 |
| refactor | 코드 리팩토링 |
| test | 테스트 코드 |
| style | 포맷, 린트 수정 |
| chore | 빌드, 패키지 설정 |

---

## 로컬 실행 방법

**전체 서비스 (Docker Compose)**
```bash
docker compose up -d --build
```

**백엔드 (단독)**
```bash
uv run uvicorn backend.app.main:app --reload
```

**AI 서버**
```bash
uv run uvicorn ai.main:app --reload --port 8001
```

**프론트엔드** (별도 저장소)
```bash
git clone https://github.com/OZ-DailyCare-Challenge/frontend
cd frontend
npm install
npm run dev
```

---

## 환경변수

- 경로: `envs/.local.env` (로컬), `.env` (Docker)
- 예시: `envs/example.local.env`

---

## 프로젝트 기간

2026.03.24 ~ 2026.05.07
