import uuid

import aioboto3

from app.core.config import Config

_config = Config()

_session = aioboto3.Session(
    aws_access_key_id=_config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=_config.AWS_SECRET_ACCESS_KEY,
    region_name=_config.AWS_S3_REGION,
)

_MEDIA_TYPE_TO_EXT = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


async def upload_image(image_bytes: bytes, media_type: str) -> str:
    """S3에 이미지를 업로드하고 퍼블릭 URL을 반환한다."""
    ext = _MEDIA_TYPE_TO_EXT.get(media_type, "jpg")
    key = f"vision/{uuid.uuid4().hex}.{ext}"

    async with _session.client("s3") as s3:
        await s3.put_object(
            Bucket=_config.AWS_S3_BUCKET_NAME,
            Key=key,
            Body=image_bytes,
            ContentType=media_type,
        )

    return f"https://{_config.AWS_S3_BUCKET_NAME}.s3.{_config.AWS_S3_REGION}.amazonaws.com/{key}"
