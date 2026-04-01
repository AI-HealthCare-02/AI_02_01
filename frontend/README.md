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
```
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

## 🗺 서비스 흐름

```
Login → Dashboard → Health Input → Challenge → Character 성장
```