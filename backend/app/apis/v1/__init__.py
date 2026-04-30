from fastapi import APIRouter

from app.apis.v1.ai_vision_routers import ai_vision_router
from app.apis.v1.analysis_routers import analysis_router
from app.apis.v1.auth_routers import auth_router
from app.apis.v1.challenge_routers import challenge_router, user_challenge_router
from app.apis.v1.checkup_routers import checkup_router
from app.apis.v1.health_routers import health_router
from app.apis.v1.social_routers import social_router
from app.apis.v1.user_routers import user_router

v1_routers = APIRouter(prefix="/api/v1")
v1_routers.include_router(analysis_router)
v1_routers.include_router(auth_router)
v1_routers.include_router(health_router)
v1_routers.include_router(social_router)
v1_routers.include_router(user_router)
v1_routers.include_router(ai_vision_router)
v1_routers.include_router(challenge_router)
v1_routers.include_router(user_challenge_router)
v1_routers.include_router(checkup_router)
