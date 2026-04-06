from pydantic import BaseModel, ConfigDict


class BaseSerializerModel(BaseModel):
    """
    Response DTO 전용 공통 부모 클래스.

    - from_attributes=True: SQLAlchemy 모델 객체를 Pydantic 모델로 직접 변환 가능하게 설정
      - 미설정 시: model_validate(user) 호출 시 dict만 허용, SQLAlchemy 객체 전달 시 에러 발생
      - 설정 시: SQLAlchemy 객체의 속성(.nickname, .email 등)을 자동으로 읽어 Pydantic 필드에 매핑
    - Request DTO는 JSON dict를 받으므로 BaseModel을 직접 상속
    - Response DTO는 SQLAlchemy 객체 변환이 필요하므로 이 클래스를 상속
    """

    model_config = ConfigDict(from_attributes=True)
