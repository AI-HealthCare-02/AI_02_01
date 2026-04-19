"""
ML2 Vision 이미지 분석 성능 테스트 시나리오

테스트 흐름:
1. POST /api/v1/ai/meals/free  → 식단 분석 요청 (multipart/form-data)
2. task_id 수신
3. GET /api/v1/ai/tasks/{task_id}/wait  → 롱 폴링으로 결과 대기

사전 준비:
- tests/performance/assets/ 폴더에 test_meal.jpg 파일 필요
"""

import os

from locust import HttpUser, between, task

# 테스트 이미지 경로 (tests/performance/assets/test_meal.jpg)
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
MEAL_IMAGE_PATH = os.path.join(ASSETS_DIR, "test_meal.jpg")
EXERCISE_IMAGE_PATH = os.path.join(ASSETS_DIR, "test_exercise.jpg")


class ML2VisionUser(HttpUser):
    """
    ML2 Vision 분석 전체 흐름 테스트 유저.
    - wait_time: Vision API는 처리 시간이 길어 여유 있게 설정
    """

    wait_time = between(3, 7)

    @task(2)
    def meal_analysis_flow(self):
        """
        식단 무료 분석 전체 흐름 테스트.
        이미지 업로드 → 롱 폴링으로 결과 수신까지 측정.
        """
        if not os.path.exists(MEAL_IMAGE_PATH):
            # 테스트 이미지 없으면 스킵
            return

        # 1. 식단 분석 요청 (multipart/form-data)
        with open(MEAL_IMAGE_PATH, "rb") as image_file:
            with self.client.post(
                "/api/v1/ai/meals/free",
                files={"image": ("test_meal.jpg", image_file, "image/jpeg")},
                name="ML2 | POST 식단 분석 요청",
                catch_response=True,
            ) as response:
                if response.status_code != 202:
                    response.failure(f"식단 분석 요청 실패: {response.status_code}")
                    return

                data = response.json()

        task_id = data.get("task_id")
        if not task_id:
            return

        # 2. 롱 폴링으로 결과 대기 (최대 30초)
        with self.client.get(
            f"/api/v1/ai/tasks/{task_id}/wait",
            name="ML2 | GET 식단 결과 대기 (롱 폴링)",
            catch_response=True,
            timeout=35,
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if result.get("status") != "success":
                    response.failure(f"예상치 못한 상태값: {result.get('status')}")
            elif response.status_code == 408:
                response.failure("롱 폴링 타임아웃 (30초 초과)")
            else:
                response.failure(f"롱 폴링 실패: {response.status_code}")

    @task(1)
    def exercise_analysis_flow(self):
        """
        운동 인증 분석 전체 흐름 테스트.
        """
        if not os.path.exists(EXERCISE_IMAGE_PATH):
            return

        with open(EXERCISE_IMAGE_PATH, "rb") as image_file:
            with self.client.post(
                "/api/v1/ai/exercise",
                files={"image": ("test_exercise.jpg", image_file, "image/jpeg")},
                name="ML2 | POST 운동 인증 요청",
                catch_response=True,
            ) as response:
                if response.status_code != 202:
                    response.failure(f"운동 인증 요청 실패: {response.status_code}")
                    return

                data = response.json()

        task_id = data.get("task_id")
        if not task_id:
            return

        with self.client.get(
            f"/api/v1/ai/tasks/{task_id}/wait",
            name="ML2 | GET 운동 결과 대기 (롱 폴링)",
            catch_response=True,
            timeout=35,
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if result.get("status") != "success":
                    response.failure(f"예상치 못한 상태값: {result.get('status')}")
            elif response.status_code == 408:
                response.failure("롱 폴링 타임아웃 (30초 초과)")
            else:
                response.failure(f"롱 폴링 실패: {response.status_code}")
