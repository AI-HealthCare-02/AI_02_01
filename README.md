# 만성질환 챌린지 웹 서비스

> 건강검진 수치 입력 → 심혈관 위험도 예측 → 위험 요인별 챌린지 추천

---

## 서비스 소개

건강검진 수치를 입력하면 XGBoost 모델이 심혈관 위험도(%)와 심혈관 나이를 예측하고,
주요 위험 요인에 맞는 생활습관 챌린지를 자동으로 추천하는 웹 서비스입니다.
매일 챌린지를 수행하면 위험도가 재예측되어 건강 개선 효과를 직접 확인할 수 있습니다.

---

## 팀원

| 이름 | 역할 |
|---|---|
| 조영현 | Backend (Main) / Frontend (Sub) |
| 박소윤 | Frontend (Main) / Backend (Sub) |
| 이승희 | AI (Main) / Data Analysis (Sub) |
| 이형석 | Data Engineer (Main) / Frontend (Sub) |

---

## 기술 스택

**Frontend**
- React, Vite, Tailwind CSS, Chart.js

**Backend**
- FastAPI, PostgreSQL, SQLAlchemy
- Google OAuth 2.0 + JWT

**AI / Data**
- XGBoost, SHAP, scikit-learn
- Claude API (건강 코멘트 생성)
- Pandas, NumPy, Matplotlib, Seaborn

**Infra**
- Docker Compose, GitHub Actions

---

## 프로젝트 구조
```
chronic_challenge/
├── frontend/        # React 프론트엔드
├── backend/         # FastAPI 백엔드
├── ai/              # ML 모델 + Claude API
│   ├── notebooks/   # EDA, 전처리, 모델 학습
│   ├── models/      # 저장된 모델 파일
│   └── data/        # 데이터셋 (Git 제외)
└── data/            # 공통 데이터
```

---

## 브랜치 전략
```
main
└── develop
    ├── feature/frontend
    ├── feature/backend
    ├── feature/ai
    └── feature/data
```

- `feature/*` → `develop` : PR + 리뷰어 1명 승인
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
| chore | 빌드, 패키지 설정 |

---

## 로컬 실행 방법

**백엔드**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**프론트엔드**
```bash
cd frontend
npm install
npm run dev
```

**AI**
```bash
cd ai
conda activate ml_env
jupyter notebook notebooks/
```

---

## 프로젝트 기간

2026.03.24 ~ 2026.05.07
