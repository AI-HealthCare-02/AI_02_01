from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.databases import get_db_session
from app.models.users import User
from app.repositories.user_repository import UserRepository
from app.services.jwt import JwtService

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_request_user(
    credential: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    token = credential.credentials
    verified = JwtService().verify_jwt(token=token, token_type="access")
    user_id = verified.payload.get("id")
    if user_id is None:
        raise HTTPException(detail="Authenticate Failed.", status_code=status.HTTP_401_UNAUTHORIZED)
    user = await UserRepository(session).get_user(user_id)
    if not user or user.is_deleted:
        raise HTTPException(detail="Authenticate Failed.", status_code=status.HTTP_401_UNAUTHORIZED)
    return user


async def get_optional_user(
    credential: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_security)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User | None:
    if not credential:
        return None
    try:
        token = credential.credentials
        verified = JwtService().verify_jwt(token=token, token_type="access")
        user_id = verified.payload.get("id")
        if user_id is None:
            return None
        user = await UserRepository(session).get_user(user_id)
        if not user or user.is_deleted:
            return None
        return user
    except Exception:
        return None
