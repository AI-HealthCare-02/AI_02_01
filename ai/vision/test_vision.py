import base64
from pathlib import Path

from ai.vision.tasks import analyze_meal_paid
from ai.vision.tasks import analyze_exercise

# IMAGE_PATH = Path("ai/vision/test_images/test.png") # 운동인증
IMAGE_PATH = Path("ai/vision/test_images/test.jpg") # 식단인증

def main():
    if not IMAGE_PATH.exists():
        print(f"이미지 파일이 없음: {IMAGE_PATH}")
        return

    with open(IMAGE_PATH, "rb") as f:
        image_bytes = f.read()

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
# 식단
    result = analyze_meal_paid.delay(
        image_base64=image_base64,
        media_type="image/jpeg"
    )
# 운동
#     result = analyze_exercise.delay(    
#     image_base64=image_base64,
#     media_type="image/png"
# )

    print("Task ID:", result.id)
    print("Waiting for result...")

    response = result.get(timeout=120)

    print("Result:")
    print(response)


if __name__ == "__main__":
    main()