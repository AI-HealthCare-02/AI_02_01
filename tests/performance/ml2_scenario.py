"""
ML2 Vision 이미지 분석 성능 테스트 시나리오

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Locust 전체 동작 단계 (이 파일이 관여하는 단계 표시)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1단계. 명령어 실행         bash tests/performance/run_ml2_test.sh 1
         → [Locust 프레임워크 처리 / 이 파일 관여 없음]

2단계. 시나리오 파일 로드  ml2_scenario.py 임포트
         → 파일 최상단 코드 1회 실행 (import, 상수 정의, 클래스 정의)
         → [이 파일의 모듈 레벨 코드 전체]                  ← 이 파일 관여

3단계. 웹 UI 시작          http://localhost:8089 열림
         → [Locust 프레임워크 처리 / 이 파일 관여 없음]

4단계. 가상 유저 생성      ML2VisionUser 인스턴스 N개 생성
         → [Locust 프레임워크가 HttpUser 클래스를 인스턴스화] ← 이 파일의 클래스 정의 사용

5단계. 유저 초기화         on_start() 1회 실행
         → JWT 헤더 설정, 이미지 파일 존재 여부 확인
         → [ML2VisionUser.on_start()]                        ← 이 파일 관여

6단계. 태스크 루프         태스크 선택 → 실행 → 대기 무한 반복
         → 가중치 기반 랜덤 선택: 식단 분석(67%) / 운동 인증(33%)
         → [ML2VisionUser의 @task 메서드들]                  ← 이 파일 관여

7단계. API 호출 / AI 분석  Locust는 HTTP 요청만 담당, AI 분석은 EC2에서 실행
         → Locust(로컬): self.client.post/get → 요청 전송 + 응답 시간 측정
         → EC2 FastAPI : JWT 검증 → 이미지 인코딩 → Celery 태스크 생성
         → EC2 ai-worker: Claude Vision API 호출 (실제 AI 분석)
         → EC2 FastAPI : 롱폴링으로 결과 수신 → 응답 반환
         → [@task 메서드 내 self.client 호출 부분]            ← 이 파일 관여

8단계. 통계 수집           응답 시간/실패율 실시간 집계 후 웹 UI 표시
         → [Locust 프레임워크 처리 / name= 파라미터는 이 파일에서 정의] ← 이 파일 관여

9단계. 종료                Stop 클릭 또는 Ctrl+C
         → [Locust 프레임워크 처리 / 이 파일 관여 없음]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

엔드포인트:
1. POST /api/v1/ai/meals/free           → 식단 이미지 무료 분석 (JWT 필수)
2. POST /api/v1/ai/exercise             → 운동 인증 이미지 분석 (JWT 필수)
3. GET  /api/v1/ai/tasks/{task_id}/wait → 롱 폴링 결과 대기 (JWT 불필요)

ML2 캐시 구조:
  ML2에는 ML1과 달리 Redis 캐시가 없다.
  enqueue_meal_free / enqueue_exercise는 캐시 확인 없이 바로 Celery 태스크를 등록한다.
  → 동일한 이미지를 반복 전송해도 매번 새로운 Claude Vision API 호출 발생
  → 캐시 포화 문제 없음 → 별도 데이터 랜덤화 불필요

ML1 vs ML2 차이:
  ML1: XGBoost 로컬 모델, 처리 1~5초, Redis 캐시 있음, 비회원 엔드포인트 존재
  ML2: Claude Vision 외부 API, 처리 10~25초, 캐시 없음, JWT 인증 필수

타임아웃 계층:
  서버: asyncio.timeout(30) → 30초 초과 시 408 반환
  클라이언트: timeout=35 → 서버 30초 + 네트워크 여유 5초

실행 방법:
    export ML2_TEST_TOKEN="eyJ..."
    bash tests/performance/run_ml2_test.sh 1

환경변수:
    ML2_TEST_TOKEN: JWT access_token (필수 — 미설정 시 모든 태스크 스킵)
"""

# ──────────────────────────────────────────────────────────────────────────────
# [2단계] 모듈 임포트
# ──────────────────────────────────────────────────────────────────────────────
import os

from locust import HttpUser, between, task


# ──────────────────────────────────────────────────────────────────────────────
# [2단계] 모듈 상수 정의
# ──────────────────────────────────────────────────────────────────────────────

# 테스트 이미지 경로
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
MEAL_IMAGE_PATH = os.path.join(ASSETS_DIR, "test_meal.jpg")
EXERCISE_IMAGE_PATH = os.path.join(ASSETS_DIR, "test_exercise.jpg")

# [2단계] JWT 토큰 (모듈 로드 시 환경변수에서 1회 읽기)
# ML2는 모든 POST 엔드포인트에 JWT 인증이 필수다.
# 미설정 시 on_start()에서 경고 출력 후 모든 태스크가 스킵된다.
TEST_TOKEN = os.environ.get("ML2_TEST_TOKEN", "")

if TEST_TOKEN:
    print("[ML2 시나리오] ML2_TEST_TOKEN 설정 확인 → 모든 태스크 활성화")
else:
    print("[ML2 시나리오] ML2_TEST_TOKEN 미설정 → 모든 태스크 스킵")
    print("  활성화 방법: uv run python scripts/gen_token.py --user-id 1")
    print("              export ML2_TEST_TOKEN='eyJ...'")


# ──────────────────────────────────────────────────────────────────────────────
# [2단계 / 4단계] 가상 유저 클래스 정의
# ──────────────────────────────────────────────────────────────────────────────
class ML2VisionUser(HttpUser):
    """
    ML2 Vision 분석 전체 흐름 테스트 유저.

    - 식단 분석 (무료): 태스크 가중치 3  →  전체의 50%
    - 운동 인증 분석   : 태스크 가중치 2  →  전체의 33%
    - 식단 분석 (유료): 태스크 가중치 1  →  전체의 17%

    Claude Vision API 호출로 인해 ML1 XGBoost보다 처리 시간이 길다. (10~25초)
    wait_time을 넉넉하게 설정하여 실제 사용자 행동을 시뮬레이션한다.
    """

    # [6단계] 태스크 완료 후 다음 태스크 선택 전 대기 시간
    # between(3, 7) → 3~7초 랜덤 대기. Vision API 처리 시간이 길어 ML1보다 여유롭게 설정
    wait_time = between(3, 7)

    # ──────────────────────────────────────────────────────────────────────────
    # [5단계] 유저 초기화
    # ──────────────────────────────────────────────────────────────────────────
    def on_start(self) -> None:
        """가상 유저 초기화: JWT 헤더 설정 및 테스트 이미지 파일 존재 여부 확인."""

        # JWT 인증 헤더 설정 (ML2 모든 POST 엔드포인트에 필수)
        if TEST_TOKEN:
            self.auth_headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
        else:
            self.auth_headers = None

        # 이미지 파일 존재 여부 확인 (없으면 해당 태스크 스킵)
        self.meal_image_available = os.path.exists(MEAL_IMAGE_PATH)
        self.exercise_image_available = os.path.exists(EXERCISE_IMAGE_PATH)

        if not self.meal_image_available:
            print(f"[ML2 시나리오] 식단 테스트 이미지 없음 → 식단 분석 태스크 스킵")
            print(f"  필요 경로: {MEAL_IMAGE_PATH}")
        if not self.exercise_image_available:
            print(f"[ML2 시나리오] 운동 테스트 이미지 없음 → 운동 인증 태스크 스킵")
            print(f"  필요 경로: {EXERCISE_IMAGE_PATH}")

    # ──────────────────────────────────────────────────────────────────────────
    # [6단계] 태스크: 식단 분석 (무료)
    # @task(3): 가중치 3 → 전체 태스크 중 50% 확률로 선택됨
    # 목적: JWT 인증 → 이미지 업로드 → Claude Vision API → 롱폴링까지 전체 처리 시간 측정
    # ──────────────────────────────────────────────────────────────────────────
    @task(3)
    def meal_analysis_flow(self) -> None:
        """식단 무료 분석 흐름: POST 이미지 업로드 (JWT) → GET 롱 폴링 결과 대기."""

        # 토큰 미설정 또는 이미지 없는 경우 즉시 반환
        if not self.auth_headers or not self.meal_image_available:
            return

        # ── [6단계 / 7단계] API 호출 1: POST /api/v1/ai/meals/free ───────────
        # 7단계 Locust 역할  : JWT 헤더 + multipart/form-data로 이미지 전송
        # 7단계 EC2 FastAPI  : JWT 검증 → 이미지 Base64 인코딩 → Celery 태스크 생성
        # 7단계 EC2 ai-worker: Claude Vision API 호출 비동기 시작
        # 캐시 없음          : ML2는 Redis 캐시가 없어 동일 이미지라도 매번 새 태스크 생성
        with open(MEAL_IMAGE_PATH, "rb") as image_file:
            with self.client.post(
                "/api/v1/ai/meals/free",
                files={"image": ("test_meal.jpg", image_file, "image/jpeg")},
                headers=self.auth_headers,         # JWT 인증 헤더 (필수)
                name="ML2 | POST 식단 분석 요청",  # [8단계] Statistics 그룹명
                catch_response=True,
            ) as response:
                if response.status_code == 401:
                    response.failure("JWT 토큰 만료 (run_ml2_test.sh 재실행으로 토큰 재발급)")
                    return
                if response.status_code != 202:
                    response.failure(f"식단 분석 요청 실패: {response.status_code}")
                    return
                data = response.json()

        task_id = data.get("task_id")
        if not task_id:
            return

        # ── [6단계 / 7단계] API 호출 2: GET /api/v1/ai/tasks/{task_id}/wait ──
        # 7단계 Locust 역할  : HTTP GET 요청 전송 + 응답 대기 + 전체 시간 측정
        # 7단계 EC2 FastAPI  : Redis Pub/Sub 채널 구독 → ai-worker 완료 알림 대기
        # 7단계 EC2 ai-worker: Claude Vision API 완료 → Pub/Sub 발행
        # 7단계 EC2 FastAPI  : 알림 수신 → 결과 반환 → HTTP 연결 종료
        # 8단계 통계 기록    : 이 응답 시간 = Claude Vision API 처리 시간 포함
        # timeout=35         : 서버 롱폴링 30초 + 네트워크 여유 5초
        # JWT 불필요         : /wait 엔드포인트는 task_id만으로 접근 가능
        #
        # [상태값 주의]
        # ML2 응답의 status는 대문자 "SUCCESS" (ML1의 "success"와 다름)
        with self.client.get(
            f"/api/v1/ai/tasks/{task_id}/wait",
            name="ML2 | GET 식단 결과 대기 (롱 폴링)",  # [8단계] Statistics 그룹명
            catch_response=True,
            timeout=35,
        ) as response:
            if response.status_code == 200:
                result = response.json()
                # ML2 status는 대문자 "SUCCESS" — ML1의 "success"와 다름
                if result.get("status", "").upper() != "SUCCESS":
                    response.failure(f"예상치 못한 상태값: {result.get('status')}")
            elif response.status_code == 408:
                # 30초 내 Claude Vision API 미완료 → AI Worker 과부하 또는 Claude API 지연
                response.failure("롱 폴링 타임아웃 (30초 초과)")
            else:
                response.failure(f"롱 폴링 실패: {response.status_code}")

    # ──────────────────────────────────────────────────────────────────────────
    # [6단계] 태스크: 운동 인증 분석
    # @task(2): 가중치 2 → 전체 태스크 중 33% 확률로 선택됨
    # 목적: JWT 인증 → 운동 이미지 업로드 → Claude Vision API → 롱폴링 처리 시간 측정
    # ──────────────────────────────────────────────────────────────────────────
    @task(2)
    def exercise_analysis_flow(self) -> None:
        """운동 인증 분석 흐름: POST 이미지 업로드 (JWT) → GET 롱 폴링 결과 대기."""

        # 토큰 미설정 또는 이미지 없는 경우 즉시 반환
        if not self.auth_headers or not self.exercise_image_available:
            return

        # ── [6단계 / 7단계] API 호출 1: POST /api/v1/ai/exercise ────────────
        # 7단계 Locust 역할  : JWT 헤더 + multipart/form-data로 이미지 전송
        # 7단계 EC2 FastAPI  : JWT 검증 → 이미지 Base64 인코딩 → Celery 태스크 생성
        # 7단계 EC2 ai-worker: Claude Vision API로 운동 인증 여부 비동기 분석 시작
        with open(EXERCISE_IMAGE_PATH, "rb") as image_file:
            with self.client.post(
                "/api/v1/ai/exercise",
                files={"image": ("test_exercise.jpg", image_file, "image/jpeg")},
                headers=self.auth_headers,         # JWT 인증 헤더 (필수)
                name="ML2 | POST 운동 인증 요청",  # [8단계] Statistics 그룹명
                catch_response=True,
            ) as response:
                if response.status_code == 401:
                    response.failure("JWT 토큰 만료 (run_ml2_test.sh 재실행으로 토큰 재발급)")
                    return
                if response.status_code != 202:
                    response.failure(f"운동 인증 요청 실패: {response.status_code}")
                    return
                data = response.json()

        task_id = data.get("task_id")
        if not task_id:
            return

        # ── [6단계 / 7단계] API 호출 2: GET /api/v1/ai/tasks/{task_id}/wait ──
        # JWT 불필요: /wait 엔드포인트는 task_id만으로 접근 가능
        with self.client.get(
            f"/api/v1/ai/tasks/{task_id}/wait",
            name="ML2 | GET 운동 결과 대기 (롱 폴링)",  # [8단계] Statistics 그룹명
            catch_response=True,
            timeout=35,
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if result.get("status", "").upper() != "SUCCESS":
                    response.failure(f"예상치 못한 상태값: {result.get('status')}")
            elif response.status_code == 408:
                response.failure("롱 폴링 타임아웃 (30초 초과)")
            else:
                response.failure(f"롱 폴링 실패: {response.status_code}")


    # ──────────────────────────────────────────────────────────────────────────
    # [6단계] 태스크: 식단 분석 (유료)
    # @task(1): 가중치 1 → 전체 태스크 중 17% 확률로 선택됨
    # 목적: 유료 상세 리포트 API의 처리 시간 측정 (무료와 동일 Claude API, 프롬프트 상이)
    # 전제: 테스트 유저 계정에 포인트(300pt 이상)가 충분해야 한다
    # ──────────────────────────────────────────────────────────────────────────
    @task(1)
    def meal_paid_analysis_flow(self) -> None:
        """식단 유료 분석 흐름: POST 이미지 업로드 (JWT, -300pt) → GET 롱 폴링 결과 대기."""

        # 토큰 미설정 또는 이미지 없는 경우 즉시 반환
        if not self.auth_headers or not self.meal_image_available:
            return

        # ── [6단계 / 7단계] API 호출 1: POST /api/v1/ai/meals/paid ──────────
        # 7단계 Locust 역할  : JWT 헤더 + multipart/form-data로 이미지 전송
        # 7단계 EC2 FastAPI  : JWT 검증 → 포인트 확인 → 이미지 인코딩 → Celery 태스크 생성
        # 7단계 EC2 ai-worker: 비타민/미네랄/나트륨 포함 상세 리포트용 Claude Vision API 호출
        # 402 처리           : 포인트 부족 시 스킵 (실패로 기록하지 않음)
        with open(MEAL_IMAGE_PATH, "rb") as image_file:
            with self.client.post(
                "/api/v1/ai/meals/paid",
                files={"image": ("test_meal.jpg", image_file, "image/jpeg")},
                headers=self.auth_headers,
                name="ML2 | POST 식단 유료 분석 요청",  # [8단계] Statistics 그룹명
                catch_response=True,
            ) as response:
                if response.status_code == 401:
                    response.failure("JWT 토큰 만료 (run_ml2_test.sh 재실행으로 토큰 재발급)")
                    return
                if response.status_code == 402:
                    # 포인트 부족 → 실패로 기록하지 않고 스킵 (정상적인 비즈니스 제한)
                    response.success()
                    return
                if response.status_code != 202:
                    response.failure(f"식단 유료 분석 요청 실패: {response.status_code}")
                    return
                data = response.json()

        task_id = data.get("task_id")
        if not task_id:
            return

        # ── [6단계 / 7단계] API 호출 2: GET /api/v1/ai/tasks/{task_id}/wait ──
        # 무료 분석과 동일한 롱 폴링 엔드포인트 사용 (task_id 기반, JWT 불필요)
        with self.client.get(
            f"/api/v1/ai/tasks/{task_id}/wait",
            name="ML2 | GET 식단 유료 결과 대기 (롱 폴링)",  # [8단계] Statistics 그룹명
            catch_response=True,
            timeout=35,
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if result.get("status", "").upper() != "SUCCESS":
                    response.failure(f"예상치 못한 상태값: {result.get('status')}")
            elif response.status_code == 408:
                response.failure("롱 폴링 타임아웃 (30초 초과)")
            else:
                response.failure(f"롱 폴링 실패: {response.status_code}")


# ──────────────────────────────────────────────────────────────────────────────
# [9단계] 종료
# → 이 파일에서 별도로 작성할 코드 없음 (Locust 프레임워크가 자동 처리)
# ──────────────────────────────────────────────────────────────────────────────
