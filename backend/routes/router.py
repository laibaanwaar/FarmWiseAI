from fastapi import APIRouter

from backend.routes.auth_routes import router as auth_router
from backend.routes.chat_routes import router as chat_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(chat_router)
