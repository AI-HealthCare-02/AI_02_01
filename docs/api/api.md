# API 명세서

> 마이헬스버디 (MyHealthBuddy) - 전체 API 명세

원본: [Notion](https://far-octagon-170.notion.site/API-330e5d4a0bac800d9bebfb05d9209c3e)

---

## 목차

| Domain | Prefix | API 수 |
|---|---|---|
| [인증 (SEC)](#인증-sec) | `/api/v1/auth` | 2 |
| [사용자 (USER)](#사용자-user) | `/api/v1/users` | 4 |
| [건강데이터 (HLTH)](#건강데이터-hlth) | `/api/v1/health` | 9 |
| [Vision AI](#vision-ai) | `/api/v1/ai` | 4 |
| [소셜 (SOCL)](#소셜-socl) | `/api/v1/social` | 7 |

---

## 인증 (SEC)

### 소셜 로그인 / 회원가입

> Google 인가 코드를 받아 로그인 또는 신규 회원가입을 처리한다. 기존 회원이면 200, 신규 가입이면 201을 반환한다.

- **메서드:** `POST`
- **엔드포인트:** `/api/v1/auth/login/{provider}`
- **인증:** 불필요

**요구사항**
- `provider`는 현재 `google`만 지원
- 인가 코드(`code`)는 1회용이며 10분 내 사용 필요
- `access_token`은 응답 body에 포함
- `refresh_token`은 httponly 쿠키에 저장 (XSS 방어)
- 탈퇴 계정(`is_active=False`)은 423 반환

**Path Parameter**

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| provider | string | Y | 소셜 로그인 제공자 (google) |

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| code | string | Y | Google OAuth2 인가 코드 |

**Response - 200 OK (기존 회원) / 201 Created (신규 회원)**

| 필드 | 타입 | 설명 |
|---|---|---|
| is_new_user | boolean | 신규 가입 여부 |
| access_token | string | JWT Access Token |
| user.id | int | 사용자 ID |
| user.email | string | 이메일 |
| user.nickname | string | 닉네임 |
| user.profile_image | string | 프로필 이미지 URL |
| user.gender | string | 성별 (M/F, 초기 미설정 시 null) |
| user.age | int | 나이 (초기 미설정 시 null) |

**Error**

| 코드 | 설명 |
|---|---|
| 400 | 지원하지 않는 provider 또는 유효하지 않은 인가 코드 |
| 422 | 요청 데이터 형식 오류 (code 필드 누락) |
| 423 | 비활성화된(탈퇴한) 계정 |
| 502 | Google 서버 통신 오류 |

---

### Access Token 갱신

> httponly 쿠키에 저장된 Refresh Token을 검증하고 새로운 Access Token을 발급한다.

- **메서드:** `GET`
- **엔드포인트:** `/api/v1/auth/token/refresh`
- **인증:** 불필요 (쿠키 자동 전송)

**요구사항**
- `refresh_token` 쿠키가 없으면 401 반환
- `refresh_token` 만료 시 401 반환 (재로그인 필요)
- `refresh_token` 유효기간: 14일

**Cookie (자동 전송)**

| 필드 | 타입 | 설명 |
|---|---|---|
| refresh_token | string | httponly 쿠키로 저장된 Refresh Token |

**Response - 200 OK**

| 필드 | 타입 | 설명 |
|---|---|---|
| access_token | string | 새로 발급된 JWT Access Token |

**Error**

| 코드 | 설명 |
|---|---|
| 400 | 유효하지 않은 Refresh Token |
| 401 | Refresh Token 없음 또는 만료 |

---

## 사용자 (USER)

### 초기 프로필 설정

> Google 로그인 직후 성별과 출생 연도를 최초 1회 입력한다. 나이는 서버에서 자동 계산된다.

- **메서드:** `PUT`
- **엔드포인트:** `/api/v1/users/profile/initial`
- **인증:** 필요 (Bearer Token)

**요구사항**
- 성별(`gender`)은 최초 1회만 설정 가능 → 이미 설정된 경우 409 반환
- `birth_year` 범위: 1900~2026
- 나이 계산: 현재 연도 - birth_year + 1 (한국식 나이)
- `nickname`은 선택 입력 (미입력 시 기존 값 유지)

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| gender | string | Y | 성별 (M 또는 F) |
| birth_year | int | Y | 출생 연도 (1900~2026) |
| nickname | string | N | 닉네임 (미입력 시 기존 값 유지) |

**Response - 200 OK**

| 필드 | 타입 | 설명 |
|---|---|---|
| id | int | 사용자 ID |
| email | string | 이메일 |
| nickname | string | 닉네임 |
| gender | string | 성별 |
| age | int | 자동 계산된 나이 |
| profile_image | string | 프로필 이미지 URL |

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 (토큰 없음 또는 만료) |
| 409 | 이미 초기 프로필이 설정된 사용자 |

---

### 프로필 수정

> 로그인한 사용자의 닉네임, 프로필 이미지, 출생 연도를 수정한다. 출생 연도 변경 시 나이가 자동 재계산된다.

- **메서드:** `PATCH`
- **엔드포인트:** `/api/v1/users/profile`
- **인증:** 필요 (Bearer Token)

**요구사항**
- 성별(`gender`)은 수정 불가
- 수정할 필드만 포함 가능 (PATCH)
- `birth_year` 변경 시 `age` 자동 재계산

**Request Body (수정할 필드만 포함)**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| nickname | string | N | 닉네임 |
| profile_image | string | N | 프로필 이미지 URL |
| birth_year | int | N | 출생 연도 (1900~2026) |

**Response - 200 OK**

| 필드 | 타입 | 설명 |
|---|---|---|
| id | int | 사용자 ID |
| email | string | 이메일 |
| nickname | string | 닉네임 |
| gender | string | 성별 |
| age | int | 나이 (birth_year 변경 시 재계산) |
| profile_image | string | 프로필 이미지 URL |

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |

---

### 마이페이지 대시보드 조회

> 로그인한 사용자의 건강 현황 요약 정보를 반환한다.

- **메서드:** `GET`
- **엔드포인트:** `/api/v1/users/dashboard`
- **인증:** 필요 (Bearer Token)

**요구사항**
- 최근 건강검진 기록 기반 요약 정보 제공

**Response - 200 OK**

사용자 건강 현황 요약 데이터 반환

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |

---

### 회원 탈퇴

> 로그인한 사용자의 계정과 모든 관련 데이터를 영구적으로 삭제한다.

- **메서드:** `DELETE`
- **엔드포인트:** `/api/v1/users/withdraw`
- **인증:** 필요 (Bearer Token)

**요구사항**
- 본인 계정만 탈퇴 가능
- 탈퇴 후 동일 Google 계정으로 재가입 가능

**Response - 200 OK**

| 필드 | 타입 | 설명 |
|---|---|---|
| message | string | 회원 탈퇴가 완료되었습니다. |

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |

---

## 건강데이터 (HLTH)

### 건강검진 기록 생성

> 건강검진 수치를 입력하여 새로운 기록을 생성한다. BMI는 키와 몸무게를 기반으로 서버에서 자동 계산된다.

- **메서드:** `POST`
- **엔드포인트:** `/api/v1/health/records`
- **인증:** 필요 (Bearer Token)

**요구사항**
- `height`: 100~300cm (100 미만 입력 시 BMI 오버플로우 방지)
- `weight`: 10~500kg
- `systolic_bp`: 50~300 mmHg
- `diastolic_bp`: 30~200 mmHg
- `total_cholesterol`: 50~500 mg/dL
- `glucose`: 30~600 mg/dL
- BMI 자동 계산: weight / (height_m)²

**Request Body**

| 필드 | 타입 | 범위 | 필수 | 설명 |
|---|---|---|---|---|
| systolic_bp | int | 50~300 | Y | 수축기 혈압 (mmHg) |
| diastolic_bp | int | 30~200 | Y | 이완기 혈압 (mmHg) |
| total_cholesterol | int | 50~500 | Y | 총 콜레스테롤 (mg/dL) |
| glucose | int | 30~600 | Y | 공복 혈당 (mg/dL) |
| height | float | 100~300 | Y | 키 (cm) |
| weight | float | 10~500 | Y | 몸무게 (kg) |
| smoke_yn | boolean | - | Y | 흡연 여부 |
| alcohol_yn | boolean | - | Y | 음주 여부 |
| exercise_yn | boolean | - | Y | 규칙적 운동 여부 |

**Response - 201 Created**

| 필드 | 타입 | 설명 |
|---|---|---|
| id | int | 기록 ID |
| user_id | int | 사용자 ID |
| systolic_bp | int | 수축기 혈압 |
| diastolic_bp | int | 이완기 혈압 |
| total_cholesterol | int | 총 콜레스테롤 |
| glucose | int | 혈당 |
| height | float | 키 |
| weight | float | 몸무게 |
| bmi | float | 자동 계산된 BMI |
| smoke_yn | boolean | 흡연 여부 |
| alcohol_yn | boolean | 음주 여부 |
| exercise_yn | boolean | 운동 여부 |
| created_at | datetime | 생성 시각 |

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |
| 422 | 입력값 유효성 오류 (범위 초과 등) |

---

### 건강검진 기록 목록 조회

> 로그인한 사용자의 건강검진 기록을 최신순으로 전체 조회한다.

- **메서드:** `GET`
- **엔드포인트:** `/api/v1/health/records`
- **인증:** 필요 (Bearer Token)

**요구사항**
- 본인 기록만 조회 가능
- 최신순 정렬

**Response - 200 OK**

| 필드 | 타입 | 설명 |
|---|---|---|
| records | array | 건강검진 기록 목록 (최신순) |
| records[].id | int | 기록 ID |
| records[].bmi | float | BMI |
| records[].created_at | datetime | 생성 시각 |
| (기타 건강수치 필드 포함) | - | - |

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |

---

### 건강검진 기록 단건 조회

> 건강검진 기록 ID로 특정 기록 1건을 조회한다.

- **메서드:** `GET`
- **엔드포인트:** `/api/v1/health/records/{record_id}`
- **인증:** 필요 (Bearer Token)

**Path Parameter**

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| record_id | int | Y | 건강검진 기록 ID |

**Response - 200 OK**

건강검진 기록 단건 데이터 반환 (생성 API 응답과 동일 구조)

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |
| 404 | 기록 없음 |

---

### 건강검진 기록 수정

> 건강검진 기록을 부분 수정한다. 본인의 기록만 수정 가능하며, 키/몸무게 변경 시 BMI가 자동 재계산된다.

- **메서드:** `PATCH`
- **엔드포인트:** `/api/v1/health/records/{record_id}`
- **인증:** 필요 (Bearer Token)

**요구사항**
- 본인 기록만 수정 가능 (타인 기록 수정 시 403)
- 수정할 필드만 포함 가능 (PATCH)
- `height`/`weight` 변경 시 BMI 자동 재계산

**Path Parameter**

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| record_id | int | Y | 건강검진 기록 ID |

**Request Body (수정할 필드만 포함)**

| 필드 | 타입 | 범위 | 설명 |
|---|---|---|---|
| systolic_bp | int | 50~300 | 수축기 혈압 |
| diastolic_bp | int | 30~200 | 이완기 혈압 |
| total_cholesterol | int | 50~500 | 총 콜레스테롤 |
| glucose | int | 30~600 | 혈당 |
| height | float | 100~300 | 키 (변경 시 BMI 재계산) |
| weight | float | 10~500 | 몸무게 (변경 시 BMI 재계산) |
| smoke_yn | boolean | - | 흡연 여부 |
| alcohol_yn | boolean | - | 음주 여부 |
| exercise_yn | boolean | - | 운동 여부 |

**Response - 200 OK**

수정된 건강검진 기록 반환 (생성 API 응답과 동일 구조)

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |
| 403 | 타인의 기록 수정 시도 |
| 404 | 기록 없음 |

---

### 건강검진 기록 삭제

> 건강검진 기록을 영구 삭제한다. 본인의 기록만 삭제 가능하다.

- **메서드:** `DELETE`
- **엔드포인트:** `/api/v1/health/records/{record_id}`
- **인증:** 필요 (Bearer Token)

**요구사항**
- 본인 기록만 삭제 가능 (타인 기록 삭제 시 403)
- 삭제 후 복구 불가

**Path Parameter**

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| record_id | int | Y | 건강검진 기록 ID |

**Response - 204 No Content**

응답 body 없음

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |
| 403 | 타인의 기록 삭제 시도 |
| 404 | 기록 없음 |

---

### AI 건강 분석 요청

> 건강검진 기록 ID를 기반으로 XGBoost 심혈관 위험도 예측 및 GPT-4o-mini 건강 코멘트를 요청한다. 캐시 히트 시 즉시 결과를 반환하고, 미스 시 task_id를 반환한다.

- **메서드:** `POST`
- **엔드포인트:** `/api/v1/health/analysis/{record_id}`
- **인증:** 필요 (Bearer Token)

**요구사항**
- 본인 기록에 대해서만 분석 요청 가능
- Redis DB2 캐시 확인 → HIT: 즉시 결과 반환 / MISS: Celery task 전송 후 task_id 반환
- 동일 입력 데이터에 대한 캐시 TTL: 24시간

**Path Parameter**

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| record_id | int | Y | 건강검진 기록 ID |

**Response - 200 OK (캐시 HIT, 즉시 결과)**

| 필드 | 타입 | 설명 |
|---|---|---|
| status | string | success |
| data.ml1_predict.risk_percent | float | 심혈관 위험도 (%) |
| data.ml1_predict.risk_grade | string | 낮음/보통/중간/높음/매우높음 |
| data.ml1_predict.heart_age | int | 심혈관 나이 |
| data.ml1_predict.character_stage | int | 캐릭터 단계 (1~5) |
| data.ml1_predict.top_risk_factors | array | 상위 3개 위험 요인 |
| data.ml1_comment.evaluation | string | 종합 건강 평가 |
| data.ml1_comment.alert | string | 긴급 경고 (없으면 null) |
| data.ml1_comment.missions | array | 맞춤 건강 미션 목록 |
| data.ml1_comment.encouragement | string | 응원 메시지 |

**Response - 200 OK (캐시 MISS, 비동기 처리)**

| 필드 | 타입 | 설명 |
|---|---|---|
| task_id | string | Celery task ID |
| status | string | pending |

**데이터 변환 규칙**

| HealthRecord 필드 | ML1 입력 필드 | 변환 규칙 |
|---|---|---|
| user.gender | gender | M→2, F→1 |
| total_cholesterol | cholesterol | <200→1, 200~239→2, ≥240→3 |
| glucose | gluc | <100→1, 100~125→2, ≥126→3 |
| smoke_yn | smoke | bool→int |
| alcohol_yn | alco | bool→int |
| exercise_yn | active | bool→int |

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |
| 403 | 타인의 기록 분석 시도 |
| 404 | 기록 없음 |

---

### 비회원 AI 건강 분석 요청

> 로그인 없이 건강 수치 입력으로 심혈관 위험도 예측을 요청한다. 생년월일(birth_date) 입력 시 만 나이 자동 계산. 캐시 히트 시 즉시 결과, 미스 시 task_id 반환.

- **메서드:** `POST`
- **엔드포인트:** `/api/v1/health/analysis/guest`
- **인증:** 불필요 (비회원)

**Request Body**

| 필드 | 타입 | 범위 | 필수 | 설명 |
|---|---|---|---|---|
| birth_date | date | YYYY-MM-DD | Y | 생년월일 (만 나이 자동 계산) |
| gender | string | M / F | Y | 성별 |
| height | float | 100~300 | Y | 키 (cm) |
| weight | float | 10~500 | Y | 몸무게 (kg) |
| systolic_bp | int | 50~300 | Y | 수축기 혈압 (mmHg) |
| diastolic_bp | int | 30~200 | Y | 이완기 혈압 (mmHg) |
| total_cholesterol | int | 50~500 | Y | 총 콜레스테롤 (mg/dL) |
| glucose | int | 30~600 | Y | 공복 혈당 (mg/dL) |
| smoke_yn | boolean | - | Y | 흡연 여부 |
| alcohol_yn | boolean | - | Y | 음주 여부 |
| exercise_yn | boolean | - | Y | 규칙적 운동 여부 |

**Response - 200 OK (캐시 HIT)** / **200 OK (캐시 MISS)**

AI 건강 분석 요청 API 응답과 동일 구조

**데이터 변환 규칙**

| 입력 필드 | ML1 입력 필드 | 변환 규칙 |
|---|---|---|
| birth_date | age | 만 나이 자동 계산 (요청 시점 기준) |
| gender | gender | M→2, F→1 |
| total_cholesterol | cholesterol | <200→1, 200~239→2, ≥240→3 |
| glucose | gluc | <100→1, 100~125→2, ≥126→3 |

**Error**

| 코드 | 설명 |
|---|---|
| 422 | 입력값 유효성 오류 (범위 초과, 미래 생년월일, 나이 1세 미만 등) |

---

### AI 분석 결과 조회

> 비동기 AI 분석 작업의 결과를 조회한다. 즉시 반환 또는 최대 30초 대기(롱 폴링) 방식을 선택할 수 있다.

#### 즉시 확인 (Polling)

- **메서드:** `GET`
- **엔드포인트:** `/api/v1/health/analysis/{task_id}`
- **인증:** 불필요
- **특징:** 현재 상태를 즉시 반환. 아직 처리 중이면 pending을 즉시 반환.

#### 롱 폴링 (Long Polling)

- **메서드:** `GET`
- **엔드포인트:** `/api/v1/health/analysis/{task_id}/wait`
- **인증:** 불필요
- **특징:** 결과가 준비될 때까지 서버에서 최대 30초 대기. Redis Pub/Sub으로 AI Worker 완료 신호 수신. 타임아웃 시 pending 반환 → 클라이언트 즉시 재요청.

**Path Parameter**

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| task_id | string | Y | AI 분석 요청 시 받은 Celery task ID |

**Response - 200 OK (분석 완료)**

| 필드 | 타입 | 설명 |
|---|---|---|
| status | string | success |
| data | object | AI 분석 결과 (분석 요청 API 응답과 동일 구조) |
| error | string | null |

**Response - 200 OK (분석 진행 중)**

| 필드 | 타입 | 설명 |
|---|---|---|
| status | string | pending |
| data | null | - |
| error | null | - |

**Response - 200 OK (분석 실패)**

| 필드 | 타입 | 설명 |
|---|---|---|
| status | string | failure / failed |
| data | null | - |
| error | string | 에러 메시지 |

**Polling 흐름**

```
[1] POST /health/analysis/{record_id}  → task_id 수신
[2] GET  /health/analysis/{task_id}    → status: pending
[3] GET  /health/analysis/{task_id}    → status: pending  (2~3초 후 재시도)
[4] GET  /health/analysis/{task_id}    → status: success  → 결과 표시
```

**즉시 확인 vs 롱 폴링 비교**

| 구분 | GET /{task_id} | GET /{task_id}/wait |
|---|---|---|
| 동작 | 즉시 반환 | 최대 30초 대기 후 반환 |
| 사용 시점 | 상태 확인, UI 표시 | 결과 수신 대기 |
| 클라이언트 재요청 | N초 후 재요청 | pending 수신 즉시 재요청 |

---

## Vision AI

> AI 서버(`/api/v1/ai`)에서 처리하는 이미지 분석 API. 결과는 태스크 ID로 비동기 조회한다.

### 식단 무료 분석 요청

> 식단 이미지를 제출하면 Vision AI 분석 태스크를 시작한다. 인증 불필요. 결과 조회 시 task_id 사용.

- **메서드:** `POST`
- **엔드포인트:** `/api/v1/ai/meals/free`
- **인증:** 불필요
- **Content-Type:** `multipart/form-data`

**Form Data**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| image | file | Y | 식단 이미지 (JPEG, PNG, WebP, GIF / 최대 20MB) |
| risk_factors | string | N | 사용자 위험 요인 (예: 고혈압, 당뇨). 미입력 시 빈 문자열 |

**Response - 202 Accepted**

| 필드 | 타입 | 설명 |
|---|---|---|
| task_id | string | Celery task ID (결과 조회 시 사용) |
| status | string | PENDING |
| message | string | 식단 무료 분석이 접수되었습니다. |

**Error**

| 코드 | 설명 |
|---|---|
| 400 | 지원하지 않는 이미지 형식 (JPEG·PNG·WebP·GIF 외) |
| 400 | 이미지 크기 20MB 초과 |

---

### 식단 유료 상세 리포트 요청

> 포인트(-300pt)를 사용하여 비타민, 미네랄, 나트륨을 포함한 상세 영양 분석 리포트를 요청한다.

- **메서드:** `POST`
- **엔드포인트:** `/api/v1/ai/meals/paid`
- **인증:** 필요 (Bearer Token)
- **Content-Type:** `multipart/form-data`

**Form Data**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| image | file | Y | 식단 이미지 (JPEG, PNG, WebP, GIF / 최대 20MB) |
| risk_factors | string | N | 사용자 위험 요인 (예: 고혈압, 당뇨) |

**Response - 202 Accepted**

| 필드 | 타입 | 설명 |
|---|---|---|
| task_id | string | Celery task ID (결과 조회 시 사용) |
| status | string | PENDING |
| message | string | 식단 유료 분석이 접수되었습니다. (-300pt) |

**무료/유료 분석 비교**

| 구분 | 무료 (meals/free) | 유료 (meals/paid) |
|---|---|---|
| 포인트 | +100pt | -300pt |
| 분석 내용 | 기본 식단 분석 | 상세 영양 분석 (비타민·미네랄·나트륨 포함) |

**Error**

| 코드 | 설명 |
|---|---|
| 400 | 지원하지 않는 이미지 형식 |
| 400 | 이미지 크기 20MB 초과 |
| 402 | 포인트 부족 |

---

### 운동 캡처 인증 요청

> 운동 앱 스크린샷을 제출하여 운동 인증을 요청한다. Vision AI가 운동 앱 화면을 인식하여 인증 여부를 판단한다.

- **메서드:** `POST`
- **엔드포인트:** `/api/v1/ai/exercise`
- **인증:** 불필요
- **Content-Type:** `multipart/form-data`

**Form Data**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| image | file | Y | 운동 앱 스크린샷 (JPEG, PNG, WebP, GIF / 최대 20MB) |

**Response - 202 Accepted**

| 필드 | 타입 | 설명 |
|---|---|---|
| task_id | string | Celery task ID (결과 조회 시 사용) |
| status | string | PENDING |
| message | string | 운동 캡처 인증이 접수되었습니다. |

**비고**
- 인증 성공 시 +100pt 지급 (포인트 처리는 결과 조회 후 처리)

**Error**

| 코드 | 설명 |
|---|---|
| 400 | 지원하지 않는 이미지 형식 |
| 400 | 이미지 크기 20MB 초과 |

---

### Vision 태스크 결과 조회

> Vision AI 분석 결과를 조회한다. 즉시 반환 또는 최대 30초 롱 폴링 방식 선택 가능.

#### 즉시 확인

- **메서드:** `GET`
- **엔드포인트:** `/api/v1/ai/tasks/{task_id}`
- **인증:** 불필요

#### 롱 폴링 (Long Polling)

- **메서드:** `GET`
- **엔드포인트:** `/api/v1/ai/tasks/{task_id}/wait`
- **인증:** 불필요
- **특징:** Redis Pub/Sub으로 AI Worker 완료 신호 수신. 최대 30초 대기. 타임아웃 시 PENDING 반환 → 클라이언트 즉시 재요청.

**Path Parameter**

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| task_id | string | Y | POST 분석 요청 시 받은 Celery task ID |

**Response - 200 OK (결과 도착)**

| 필드 | 타입 | 설명 |
|---|---|---|
| task_id | string | Celery task ID |
| status | string | SUCCESS / FAILURE |
| result | object | Vision AI 분석 결과 |
| result.status | string | success / failed |
| result.task_name | string | 태스크 이름 (예: 식단_무료_분석) |
| result.data | object | Vision AI 실제 분석 데이터 |
| result.error | string\|null | 실패 시 에러 메시지 |

**Response - 200 OK (타임아웃, 30초 초과)**

| 필드 | 타입 | 설명 |
|---|---|---|
| task_id | string | Celery task ID |
| status | string | PENDING |
| result | null | - |

**롱 폴링 동작 방식**
1. 이미 완료된 결과가 있으면 Celery backend에서 즉시 반환
2. 처리 중이면 Redis Pub/Sub 채널을 구독하고 최대 30초 대기
3. AI Worker가 분석을 완료하면 채널에 결과를 발행 → 즉시 응답 반환
4. 30초 내 결과가 오지 않으면 PENDING 반환 → 클라이언트가 즉시 재요청

---

## 소셜 (SOCL)

### 사용자 닉네임 검색

> 닉네임 키워드로 사용자를 검색한다. 자신은 제외. 각 결과에 친구 여부(is_friend) 포함. 최대 20건 반환.

- **메서드:** `GET`
- **엔드포인트:** `/api/v1/social/users/search`
- **인증:** 필요 (Bearer Token)

**Query Parameter**

| 파라미터 | 타입 | 범위 | 필수 | 설명 |
|---|---|---|---|---|
| nickname | string | 1~20자 | Y | 검색할 닉네임 키워드 (부분 일치) |

**Response - 200 OK**

| 필드 | 타입 | 설명 |
|---|---|---|
| users | array | 검색 결과 사용자 목록 (최대 20건) |
| users[].id | int | 사용자 ID |
| users[].nickname | string | 닉네임 |
| users[].profile_image | string\|null | 프로필 이미지 URL |
| users[].character_stage | int | 캐릭터 단계 (1~5) |
| users[].is_friend | boolean | 현재 로그인 사용자와의 친구 여부 |

**비고**
- 본인은 검색 결과에서 제외됨

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |
| 422 | nickname 파라미터 누락 또는 길이 초과 |

---

### 친구 요청 전송

> 특정 사용자에게 친구 요청을 전송한다. 거절된 요청은 재전송 가능.

- **메서드:** `POST`
- **엔드포인트:** `/api/v1/social/friends/request/{receiver_id}`
- **인증:** 필요 (Bearer Token)

**Path Parameter**

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| receiver_id | int | Y | 친구 요청을 받을 사용자 ID |

**Response - 201 Created**

| 필드 | 타입 | 설명 |
|---|---|---|
| request_id | int | 생성된 친구 요청 ID |
| message | string | 처리 결과 메시지 |

**비고**
- 이전에 거절된 요청은 재전송 가능
- 이미 PENDING 상태인 요청이 존재하면 오류 반환

**Error**

| 코드 | 설명 |
|---|---|
| 400 | 자기 자신에게 요청 / 이미 친구 / 진행 중인 요청 존재 / 차단 상태 |
| 401 | 인증 실패 |
| 404 | 대상 사용자 없음 |

---

### 받은 친구 요청 목록 조회

> 현재 로그인 사용자가 받은 대기 중(PENDING) 친구 요청 목록을 최신순으로 조회한다.

- **메서드:** `GET`
- **엔드포인트:** `/api/v1/social/friends/requests`
- **인증:** 필요 (Bearer Token)

**Response - 200 OK**

| 필드 | 타입 | 설명 |
|---|---|---|
| requests | array | 받은 친구 요청 목록 (최신순) |
| requests[].id | int | 친구 요청 ID |
| requests[].requester_id | int | 요청을 보낸 사용자 ID |
| requests[].requester_nickname | string | 요청을 보낸 사용자 닉네임 |
| requests[].requester_profile_image | string\|null | 프로필 이미지 URL |
| requests[].created_at | datetime | 요청 생성 시각 |

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |

---

### 친구 요청 수락

> 받은 친구 요청을 수락한다. 수락 시 양방향으로 친구 목록에 추가된다.

- **메서드:** `PATCH`
- **엔드포인트:** `/api/v1/social/friends/requests/{request_id}/accept`
- **인증:** 필요 (Bearer Token)

**Path Parameter**

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| request_id | int | Y | 수락할 친구 요청 ID |

**Response - 200 OK**

| 필드 | 타입 | 설명 |
|---|---|---|
| message | string | 처리 결과 메시지 |

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |
| 403 | 본인에게 온 요청이 아님 |
| 404 | 친구 요청 없음 |

---

### 친구 요청 거절

> 받은 친구 요청을 거절한다. 거절된 요청은 상대방이 재전송 가능.

- **메서드:** `PATCH`
- **엔드포인트:** `/api/v1/social/friends/requests/{request_id}/reject`
- **인증:** 필요 (Bearer Token)

**Path Parameter**

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| request_id | int | Y | 거절할 친구 요청 ID |

**Response - 200 OK**

| 필드 | 타입 | 설명 |
|---|---|---|
| message | string | 처리 결과 메시지 |

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |
| 403 | 본인에게 온 요청이 아님 |
| 404 | 친구 요청 없음 |

---

### 친구 목록 조회

> 현재 로그인 사용자의 친구 목록을 최신 추가 순으로 조회한다.

- **메서드:** `GET`
- **엔드포인트:** `/api/v1/social/friends`
- **인증:** 필요 (Bearer Token)

**Response - 200 OK**

| 필드 | 타입 | 설명 |
|---|---|---|
| friends | array | 친구 목록 (최신 추가 순) |
| friends[].friend_id | int | 친구 사용자 ID |
| friends[].nickname | string | 친구 닉네임 |
| friends[].profile_image | string\|null | 프로필 이미지 URL |
| friends[].character_stage | int | 캐릭터 단계 (1~5) |
| friends[].created_at | datetime | 친구 추가 시각 |

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |

---

### 친구 삭제

> 친구 관계를 삭제한다. 양방향으로 제거되며 이후 재요청 가능.

- **메서드:** `DELETE`
- **엔드포인트:** `/api/v1/social/friends/{friend_id}`
- **인증:** 필요 (Bearer Token)

**Path Parameter**

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| friend_id | int | Y | 삭제할 친구 사용자 ID |

**Response - 200 OK**

| 필드 | 타입 | 설명 |
|---|---|---|
| message | string | 처리 결과 메시지 |

**비고**
- 양방향으로 친구 관계 제거
- 삭제 후 상대방이 재요청 가능

**Error**

| 코드 | 설명 |
|---|---|
| 401 | 인증 실패 |
| 404 | 친구 관계 없음 |
