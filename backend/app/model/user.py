from sqlalchemy import Column, Boolean, Integer, String, DateTime, ForeignKey
from app.database import Base

# 사용자 테이블
class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="사용자 고유 식별자",
    )
    provider = Column(
        String,
        nullable=False,
        default="google",
        comment="소셜 로그인 제공자 (현재 google만 지원)",
    )
    provider_id = Column(
        String,
        unique=True,
        nullable=False,
        comment="소셜 로그인 제공자 고유 ID",
    )
    nickname = Column(
        String(20),
        nullable=False,
        comment="서비스 전역 닉네임 (1~20자)",
    )
    role = Column(
        String,
        nullable=False,
        default="USER",
        comment="USER / ADMIN",
    )
    gender = Column(
        String(1),
        nullable=True,
        comment="M: 남성 / F: 여성 (최초 입력 후 변경 불가)",
    )
    age = Column(
        Integer,
        nullable=True,
        comment="현재 나이 (매년 birth_year 기준 자동 +1)",
    )
    birth_year = Column(
        Integer,
        nullable=True,
        comment="출생 연도 (나이 자동 계산 기준)",
    )
    character_stage = Column(
        Integer,
        nullable=False,
        default=0,
        comment="캐릭터 진화 단계 (0~3)",
    )
    current_point = Column(
        Integer,
        nullable=False,
        default=0,
        comment="현재 보유 포인트",
    )
    is_deleted = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="탈퇴 여부 (Soft Delete)",
    )
    deleted_at = Column(
        DateTime,
        nullable=True,
        comment="탈퇴 처리 시각",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        comment="계정 생성 시각",
    )

# 친구 요청 테이블.
class Friendship(Base):
    __tablename__ = "friendships"
 
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="친구 요청 ID",
    )
    requester_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="요청 보낸 사용자 (FK → users)",
    )
    receiver_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="요청 받은 사용자 (FK → users)",
    )
    status = Column(
        String,
        nullable=False,
        default="pending",
        comment="pending / accepted / blocked",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        comment="요청 시각",
    )
 
# 친구 목록 테이블
class FriendList(Base):

    __tablename__ = "friend_list"
 
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="친구 목록 ID",
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="사용자 ID (FK → users)",
    )
    friend_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="친구 ID (FK → users)",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        comment="친구 확정 시각",
    )
 