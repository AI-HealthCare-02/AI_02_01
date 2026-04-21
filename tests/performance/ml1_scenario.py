"""
ML1 심혈관 위험도 분석 성능 테스트 시나리오

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Locust 전체 동작 단계 (이 파일이 관여하는 단계 표시)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1단계. 명령어 실행         uv run locust
         → locust.conf 자동 읽기 (host, locustfile 설정)
         → [Locust 프레임워크 처리 / 이 파일 관여 없음]

2단계. 시나리오 파일 로드  ml1_scenario.py 임포트
         → 파일 최상단 코드 1회 실행 (import, 상수 정의, 클래스 정의)
         → [이 파일의 모듈 레벨 코드 전체]                  ← 이 파일 관여

3단계. 웹 UI 시작          http://localhost:8089 열림
         → 사용자가 Number of users / Ramp up 설정
         → [Locust 프레임워크 처리 / 이 파일 관여 없음]

4단계. 가상 유저 생성      ML1AnalysisUser 인스턴스 N개 생성
         → Ramp up 속도로 순차 생성 (초당 N명씩 추가)
         → [Locust 프레임워크가 HttpUser 클래스를 인스턴스화] ← 이 파일의 클래스 정의 사용

5단계. 유저 초기화         on_start() 1회 실행
         → JWT 헤더 설정, record_id 자동 조회
         → [ML1AnalysisUser.on_start()]                      ← 이 파일 관여

6단계. 태스크 루프         태스크 선택 → 실행 → 대기 무한 반복
         → 가중치 기반 랜덤 선택: 캐시미스(50%) / 회원(33%) / 캐시히트(17%)
         → [ML1AnalysisUser의 @task 메서드들]                ← 이 파일 관여

7단계. API 호출 / AI 분석  Locust는 HTTP 요청만 담당, AI 분석은 EC2에서 실행
         → Locust(로컬): self.client.post/get → 요청 전송 + 응답 시간 측정
         → EC2 FastAPI : 요청 수신 → 캐시 확인 → Celery 태스크 생성
         → EC2 ai-worker: XGBoost 모델 실행 (실제 AI 분석)
         → EC2 FastAPI : 롱폴링으로 결과 수신 → 응답 반환
         → [@task 메서드 내 self.client 호출 부분]            ← 이 파일 관여

8단계. 통계 수집           응답 시간/실패율 실시간 집계 후 웹 UI 표시
         → name= 파라미터 기준으로 그룹핑하여 Statistics 탭에 출력
         → [Locust 프레임워크 처리 / name= 파라미터는 이 파일에서 정의] ← 이 파일 관여

9단계. 종료                Stop 클릭 또는 Ctrl+C
         → 최종 통계 터미널 출력 후 프로세스 종료
         → [Locust 프레임워크 처리 / 이 파일 관여 없음]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

엔드포인트:
1. POST /api/v1/health/analysis/guest          → 비회원 분석 (인증 불필요)
2. POST /api/v1/health/analysis/{record_id}    → 회원 분석 (JWT 토큰 필요)
3. GET  /api/v1/health/analysis/{task_id}/wait → 롱폴링 결과 대기 (공통)

실행 방법:
    # 1. 토큰 생성
    uv run python scripts/gen_token.py --user-id 1

    # 2. 환경변수 설정 후 Locust 실행
    export ML1_TEST_TOKEN="eyJ..."
    uv run locust

환경변수:
    ML1_TEST_TOKEN    : JWT access_token (필수, 미설정 시 회원 분석 태스크 스킵)
    ML1_TEST_RECORD_ID: 건강검진 기록 ID (선택, 미설정 시 on_start에서 자동 조회)
"""

# ──────────────────────────────────────────────────────────────────────────────
# [2단계] 모듈 임포트
# uv run locust 실행 시 Locust가 이 파일을 Python 모듈로 임포트한다.
# 아래 import 문은 모듈 로드 시 1회만 실행된다.
# ──────────────────────────────────────────────────────────────────────────────
import os
import random

# HttpUser  : HTTP 요청을 보내는 가상 유저의 기반 클래스 (4단계에서 인스턴스화)
# between   : wait_time에 사용 (6단계 루프에서 태스크 사이 대기 시간 지정)
# task      : 6단계 태스크 루프에서 실행할 함수를 Locust에 등록하는 데코레이터
from locust import HttpUser, between, task


# ──────────────────────────────────────────────────────────────────────────────
# [2단계] 모듈 상수 정의
# 파일 임포트 시 1회 생성된다. 모든 가상 유저 인스턴스가 동일한 데이터를 공유한다.
# ──────────────────────────────────────────────────────────────────────────────

# 캐시 히트 유도용 고정 데이터
# → 동일한 값을 반복 요청하면 서버가 Redis에서 캐시된 결과를 즉시 반환한다.
# → 7단계에서 EC2 FastAPI가 캐시 히트를 감지하면 ai-worker 없이 즉시 응답한다.
SAMPLE_HEALTH_DATA = {
    "birth_date": "1979-01-01",
    "gender": "M",
    "height": 165.0,
    "weight": 70.0,
    "systolic_bp": 140,
    "diastolic_bp": 90,
    "total_cholesterol": 200,
    "glucose": 100,
    "smoke_yn": False,
    "alcohol_yn": False,
    "exercise_yn": True,
}

# 캐시 미스 유도용 기본 데이터 (weight는 6단계 태스크 실행 시마다 랜덤 변경)
# → 매 요청마다 다른 캐시 키가 생성되어 항상 캐시 미스가 발생한다.
# → 7단계에서 EC2 ai-worker의 XGBoost 모델이 실제로 실행된다.
VARIANT_HEALTH_DATA = {
    **SAMPLE_HEALTH_DATA,
    "birth_date": "1974-06-15",
    "systolic_bp": 150,
    "diastolic_bp": 95,
    "smoke_yn": True,
    # weight는 guest_cache_miss_flow에서 random.uniform()으로 덮어씀
}

# [2단계] JWT 토큰 (모듈 로드 시 환경변수에서 1회 읽기)
# → 미설정 시 빈 문자열 반환 → 6단계 auth_analysis_flow 태스크가 자동 스킵됨
# → 모든 가상 유저 인스턴스가 동일한 토큰을 공유한다.
TEST_TOKEN = os.environ.get("ML1_TEST_TOKEN", "")

if TEST_TOKEN:
    print("[ML1 시나리오] ML1_TEST_TOKEN 설정 확인 → 회원 분석 태스크 활성화")
else:
    print("[ML1 시나리오] ML1_TEST_TOKEN 미설정 → 회원 분석 태스크 스킵")
    print("  활성화 방법: uv run python scripts/gen_token.py --user-id 1")
    print("              export ML1_TEST_TOKEN='eyJ...'")


# ──────────────────────────────────────────────────────────────────────────────
# [2단계 / 4단계] 가상 유저 클래스 정의
# 2단계: HttpUser를 상속한 클래스를 Locust가 자동으로 테스트 유저로 인식한다.
# 4단계: "Start swarming" 클릭 시 Locust가 이 클래스의 인스턴스를 N개 생성한다.
#        각 인스턴스는 독립된 가상 사용자 1명이며 자신만의 HTTP 세션을 갖는다.
# ──────────────────────────────────────────────────────────────────────────────
class ML1AnalysisUser(HttpUser):
    """
    ML1 심혈관 분석 전체 흐름 테스트 유저.
    - 비회원 분석 (캐시 미스): 태스크 가중치 3  →  전체의 50%
    - 회원 분석             : 태스크 가중치 2  →  전체의 33%
    - 비회원 분석 (캐시 히트): 태스크 가중치 1  →  전체의 17%
    """

    # [6단계] 태스크 루프에서 한 태스크 완료 후 다음 태스크 선택 전 대기 시간
    # between(1, 3) → 1초~3초 사이 랜덤 대기
    # 실제 사용자가 행동 사이에 생각하는 시간을 시뮬레이션한다.
    wait_time = between(1, 3)

    # ──────────────────────────────────────────────────────────────────────────
    # [5단계] 유저 초기화
    # 4단계에서 가상 유저 인스턴스 생성 직후 1회 호출된다.
    # 6단계 태스크 루프 시작 전에 반드시 완료된다.
    # 20명 생성 시 on_start() 20번 실행 → 터미널에 20줄 출력되는 이유.
    # ──────────────────────────────────────────────────────────────────────────
    def on_start(self) -> None:
        """가상 유저 초기화: 회원 분석에 필요한 JWT 헤더 및 record_id 설정."""
        # 인스턴스 변수로 선언 (각 가상 유저가 독립적으로 보유)
        self.record_id: int | None = None

        # 토큰이 없으면 회원 분석 관련 초기화 전부 스킵
        if not TEST_TOKEN:
            return

        # 인증 헤더 구성 (6단계 auth_analysis_flow에서 재사용)
        self.auth_headers = {"Authorization": f"Bearer {TEST_TOKEN}"}

        # 환경변수로 record_id가 직접 지정된 경우 API 조회 생략
        env_record_id = os.environ.get("ML1_TEST_RECORD_ID", "")
        if env_record_id:
            self.record_id = int(env_record_id)
            return

        # ── [5단계 / 7단계] API 호출: GET /api/v1/health/records ──────────────
        # 7단계 분류: Locust(로컬)가 HTTP 요청 전송 / EC2 FastAPI가 DB 조회 후 반환
        # 측정 여부: 8단계에서 "ML1 | GET 건강기록 조회 (초기화)"로 Statistics에 기록
        response = self.client.get(
            "/api/v1/health/records",
            headers=self.auth_headers,
            name="ML1 | GET 건강기록 조회 (초기화)",  # [8단계] Statistics 그룹명
        )
        if response.status_code == 200:
            records = response.json().get("records", [])
            if records:
                self.record_id = records[0]["id"]
                print(f"[ML1 시나리오] record_id={self.record_id} 자동 설정 완료")
        elif response.status_code == 401:
            print("[ML1 시나리오] JWT 토큰 인증 실패 → 회원 분석 태스크 스킵")

    # ──────────────────────────────────────────────────────────────────────────
    # [6단계] 태스크: 비회원 분석 (캐시 미스)
    # @task(3): 가중치 3 → 전체 태스크 중 50% 확률로 선택됨
    # 목적: 캐시 없는 상황에서 실제 AI 분석까지의 전체 응답 시간 측정
    # ──────────────────────────────────────────────────────────────────────────
    @task(3)
    def guest_cache_miss_flow(self) -> None:
        """비회원 분석 캐시 미스 흐름: POST 분석 요청 → GET 롱폴링 대기."""

        # weight를 매번 랜덤으로 변경 → 항상 새로운 캐시 키 생성 → 캐시 미스 보장
        # → 7단계에서 EC2 ai-worker의 XGBoost 모델이 실제로 실행됨
        data = {
            **VARIANT_HEALTH_DATA,
            "weight": round(random.uniform(50.0, 100.0), 1),
        }

        # ── [6단계 / 7단계] API 호출 1: POST /api/v1/health/analysis/guest ────
        # 7단계 Locust 역할  : HTTP POST 요청 전송 + 응답 시간 측정
        # 7단계 EC2 FastAPI  : 요청 수신 → 캐시 미스 확인 → Celery 태스크 생성
        # 7단계 EC2 ai-worker: 이 시점부터 XGBoost 분석 비동기 실행 시작
        # 8단계 통계 기록    : name= 값으로 Statistics에 그룹핑되어 기록됨
        # catch_response=True: 200 응답이어도 내용을 직접 검증하기 위해 사용
        with self.client.post(
            "/api/v1/health/analysis/guest",
            json=data,
            name="ML1 | POST 비회원 분석 (캐시 미스)",  # [8단계] Statistics 그룹명
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                # [8단계] response.failure() → Statistics Fails 카운트 1 증가
                response.failure(f"분석 요청 실패: {response.status_code}")
                return
            data = response.json()

        # 7단계 분기: 서버가 캐시 히트를 감지하면 status="success"로 즉시 반환
        # → 롱폴링 없이 이 태스크 종료 (6단계 루프의 다음 wait_time으로 진입)
        if data.get("status") == "success":
            return

        # 캐시 미스 시 서버는 task_id만 반환하고 분석은 백그라운드에서 계속 진행
        task_id = data.get("task_id")
        if not task_id:
            return

        # ── [6단계 / 7단계] API 호출 2: GET /api/v1/health/analysis/{task_id}/wait
        # 7단계 Locust 역할  : HTTP GET 요청 전송 + 응답 대기 + 전체 시간 측정
        # 7단계 EC2 FastAPI  : Redis Pub/Sub 채널 구독 → ai-worker 완료 알림 대기
        # 7단계 EC2 ai-worker: XGBoost 분석 완료 → Redis 저장 → Pub/Sub 발행
        # 7단계 EC2 FastAPI  : 알림 수신 → 결과 반환 → HTTP 연결 종료
        # 8단계 통계 기록    : 이 응답 시간 = 실질적인 AI 처리 시간 포함
        # timeout=35         : 서버 롱폴링 30초 + 네트워크 여유 5초
        with self.client.get(
            f"/api/v1/health/analysis/{task_id}/wait",
            name="ML1 | GET 결과 대기 (롱폴링)",  # [8단계] Statistics 그룹명
            catch_response=True,
            timeout=35,
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if result.get("status") != "success":
                    response.failure(f"예상치 못한 상태값: {result.get('status')}")
            elif response.status_code == 408:
                # 서버에서 30초 내 AI 분석이 완료되지 않은 경우
                response.failure("롱폴링 타임아웃 (30초 초과)")
            else:
                response.failure(f"롱폴링 실패: {response.status_code}")

    # ──────────────────────────────────────────────────────────────────────────
    # [6단계] 태스크: 비회원 분석 (캐시 히트)
    # @task(1): 가중치 1 → 전체 태스크 중 17% 확률로 선택됨
    # 목적: Redis 캐시 히트 시 응답 속도 측정 (7단계에서 AI 분석 없이 즉시 반환)
    # ──────────────────────────────────────────────────────────────────────────
    @task(1)
    def guest_cache_hit_flow(self) -> None:
        """비회원 분석 캐시 히트 흐름: 동일 데이터 반복 요청 → 캐시 응답 속도 측정."""

        # ── [6단계 / 7단계] API 호출: POST /api/v1/health/analysis/guest ──────
        # 7단계 Locust 역할  : HTTP POST 요청 전송 + 응답 시간 측정
        # 7단계 EC2 FastAPI  : 캐시 히트 감지 → Redis에서 결과 즉시 반환
        # 7단계 AI 분석 없음 : XGBoost 실행 안 함, ai-worker 관여 없음
        # 8단계 통계 기록    : 캐시 조회~응답까지의 시간 (보통 10~20ms)
        with self.client.post(
            "/api/v1/health/analysis/guest",
            json=SAMPLE_HEALTH_DATA,       # 매번 동일한 데이터 → 동일한 캐시 키
            name="ML1 | POST 비회원 분석 (캐시 히트)",  # [8단계] Statistics 그룹명
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"캐시 요청 실패: {response.status_code}")
                return
            data = response.json()
            # 첫 요청 시에는 아직 캐시가 없어 task_id를 반환할 수 있음
            # → 이 경우를 실패로 처리하지 않고 성공으로 기록
            if data.get("status") != "success":
                response.success()

    # ──────────────────────────────────────────────────────────────────────────
    # [6단계] 태스크: 회원 분석 (JWT 인증)
    # @task(2): 가중치 2 → 전체 태스크 중 33% 확률로 선택됨
    # 목적: 로그인 유저가 자신의 건강검진 기록으로 분석 요청하는 흐름 측정
    # 전제: 5단계 on_start()에서 TEST_TOKEN과 self.record_id가 설정되어 있어야 함
    # ──────────────────────────────────────────────────────────────────────────
    @task(2)
    def auth_analysis_flow(self) -> None:
        """회원 분석 흐름: JWT 인증 → POST 분석 요청 → GET 롱폴링 대기."""

        # 5단계 초기화 미완료 시 즉시 반환 (HTTP 요청 없음, 8단계 통계 미기록)
        if not TEST_TOKEN or not self.record_id:
            return

        # ── [6단계 / 7단계] API 호출 1: POST /api/v1/health/analysis/{record_id}
        # 7단계 Locust 역할  : JWT 헤더 포함 HTTP POST 전송 + 응답 시간 측정
        # 7단계 EC2 FastAPI  : JWT 검증 → record 소유권 확인 → 캐시 확인 → Celery 태스크 생성
        # 7단계 EC2 ai-worker: 해당 유저의 건강 데이터로 XGBoost 분석 비동기 시작
        # 8단계 통계 기록    : POST 요청~task_id 수신까지의 시간
        with self.client.post(
            f"/api/v1/health/analysis/{self.record_id}",
            headers=self.auth_headers,     # 5단계 on_start()에서 설정한 인증 헤더
            name="ML1 | POST 회원 분석 요청",  # [8단계] Statistics 그룹명
            catch_response=True,
        ) as response:
            if response.status_code == 401:
                # JWT 토큰 만료 또는 서명 불일치
                response.failure("JWT 토큰 만료 (uv run locust 재실행으로 토큰 재생성)")
                return
            if response.status_code == 403:
                # 다른 유저의 record_id로 접근 시도
                response.failure(f"record_id={self.record_id} 접근 권한 없음")
                return
            if response.status_code != 200:
                response.failure(f"분석 요청 실패: {response.status_code}")
                return
            data = response.json()

        # 7단계 분기: 이전 분석 결과 캐시 히트 시 즉시 반환
        if data.get("status") == "success":
            return

        task_id = data.get("task_id")
        if not task_id:
            return

        # ── [6단계 / 7단계] API 호출 2: GET /api/v1/health/analysis/{task_id}/wait
        # 7단계 Locust 역할  : HTTP GET 요청 전송 + 응답 대기 + 전체 시간 측정
        # 7단계 EC2 FastAPI  : Redis Pub/Sub 구독 → ai-worker 완료 알림 대기
        # 7단계 EC2 ai-worker: XGBoost 분석 완료 → Redis 저장 → Pub/Sub 발행
        # 7단계 EC2 FastAPI  : 알림 수신 → 결과 반환 → HTTP 연결 종료
        # 8단계 통계 기록    : 롱폴링 대기 시간 = 실질적인 AI 처리 시간 포함
        # 인증 불필요        : /wait 엔드포인트는 task_id만으로 접근 가능
        with self.client.get(
            f"/api/v1/health/analysis/{task_id}/wait",
            name="ML1 | GET 회원 결과 대기 (롱폴링)",  # [8단계] Statistics 그룹명
            catch_response=True,
            timeout=35,                    # 서버 30초 타임아웃 + 5초 여유
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if result.get("status") != "success":
                    response.failure(f"예상치 못한 상태값: {result.get('status')}")
            elif response.status_code == 408:
                response.failure("롱폴링 타임아웃 (30초 초과)")
            else:
                response.failure(f"롱폴링 실패: {response.status_code}")

# ──────────────────────────────────────────────────────────────────────────────
# [9단계] 종료
# 웹 UI의 Stop 클릭 또는 터미널에서 Ctrl+C 입력 시 Locust가 처리한다.
# → 모든 가상 유저의 태스크 루프 중단
# → 최종 통계(Type / Name / Reqs / Fails / Avg / Min / Max 등) 터미널 출력
# → 이 파일에서 별도로 작성할 코드 없음 (Locust 프레임워크가 자동 처리)
# ──────────────────────────────────────────────────────────────────────────────
