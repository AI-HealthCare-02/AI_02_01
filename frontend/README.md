# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])

# 🌿 MyHealthBuddy

> 만성질환 예방 및 생활습관 개선을 돕는 웹 서비스
> 건강 습관 기록 + 챌린지 + 캐릭터 보상 시스템을 결합한 플랫폼

---

## 📌 프로젝트 소개

MyHealthBuddy는 사용자가 일상 건강 습관을 기록하고, 챌린지를 통해 지속적인 건강 관리를 할 수 있도록 돕는 웹 서비스입니다.

**핵심 기능**
- 건강 습관 기록 (흡연, 음주, 운동, 걸음 수)
- 챌린지 기반 행동 유도
- 캐릭터 성장형 보상 시스템
- AI 기반 건강 피드백

---

## 🛠 기술 스택

| 기술 | 역할 |
|------|------|
| React | 컴포넌트 기반 UI 개발 |
| Vite | 빠른 개발 서버 및 빌드 |
| TypeScript | 타입 안정성 확보 |
| CSS | 스타일링 |

---

## 📁 프로젝트 구조

```
frontend/
└── src/
    ├── components/
    │   ├── Header/
    │   ├── Hero/
    │   └── Feature/
    ├── pages/
    │   ├── Landing/
    │   ├── Login/
    │   ├── Dashboard/
    │   ├── Challenge/
    │   └── HealthInput/
    ├── App.tsx
    ├── main.tsx
    └── index.css
```

---

## 🚀 시작하기

```bash
# 프로젝트 생성
npm create vite@latest frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

개발 서버: `http://localhost:5173`

---

## 📅 개발 일지

### Day 1 — 프론트엔드 환경 구축

- Vite + React + TypeScript 프로젝트 초기 세팅
- 폴더 구조 설계 (`components` / `pages` 분리)
- Landing 페이지용 기본 컴포넌트 제작 (Header, Hero, Feature)

---

### Day 2 — 로그인 기능 구현

- **Google OAuth** 로그인 방식 채택 (회원가입 없이 빠른 로그인)
- `@react-oauth/google` 라이브러리 설치

```bash
npm install @react-oauth/google
```

- 환경 변수 설정

```
# .env
VITE_GOOGLE_CLIENT_ID=your_client_id
```

- Google Cloud Console에서 OAuth Client 생성 및 origin 등록 (`http://localhost:5173`)
- Login 페이지 UI 제작 (왼쪽: 서비스 소개 / 오른쪽: 로그인 카드)

---

### Day 3 — HealthInput 페이지 및 디자인 시스템 정의

#### HealthInput 페이지 구현

사용자가 건강 검진 결과와 생활 습관 정보를 입력할 수 있는 폼을 제작했습니다.

**입력 항목 구성**

| 카테고리 | 항목 |
|----------|------|
| 기본 정보 | 닉네임, 나이, 성별, 키, 체중 |
| 건강 검진 수치 | 수축기 혈압, 이완기 혈압, 총 콜레스테롤, 공복 혈당 |
| 생활 습관 | 흡연 여부, 음주 여부, 운동 여부, 걸음 수 |

생활 습관 항목은 선택형 UI로 구현했습니다. 예/아니오 선택 후 추가 입력이 가능한 구조입니다.

```
흡연 여부
[ 예 ] [ 아니오 ]

→ 예 선택 시 추가 입력 가능
```

#### 공통 디자인 시스템 정의

서비스 전반의 UI 일관성을 위해 공통 컬러를 정의했습니다.

| 용도 | 컬러 |
|------|--|
| Primary | #6DBA7B |
| Secondary | #4C9A5F |
| Background | #E8F5EA |


- 건강 서비스에 어울리는 안정적인 그린 계열로 통일

---

### Day 4 — Landing 페이지 및 Result 페이지 구현

#### Landing 페이지

로그인 여부에 관계없이 서비스의 핵심 기능을 소개하는 시작 화면을 제작했습니다.

| 구성 요소 | 내용 |
|-----------|------|
| 서비스 소개 | 이름, 캐릭터 이미지, 핵심 문구 |
| 기능 카드 | 건강 분석 / AI 건강 코멘트 / 맞춤 챌린지 / 캐릭터 성장 |
| 진입 흐름 | 로그인 / 비로그인 분기 구조 반영 |

서비스 흐름은 아래와 같이 설계했습니다.

```
Landing → Login → Health Input → Result → Dashboard
```

#### Result 페이지

사용자가 입력한 건강 데이터를 기반으로 결과를 시각화하는 페이지를 제작했습니다.

- 건강 위험도 요약
- 주요 수치 시각화 (혈압 / 콜레스테롤 / 혈당)
- AI 건강 코멘트 영역
- 추천 챌린지 안내

```
혈압 : 정상 범위
콜레스테롤 : 주의
혈당 : 정상
```

이후 **AI 기반 건강 피드백 기능과 연결될 예정**입니다.

## 🗺 서비스 흐름

```
Login → Dashboard → Health Input → Challenge → Character 성장
```