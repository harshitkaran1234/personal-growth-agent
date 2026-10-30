from fastapi import APIRouter

from .email import router as email_router

router = APIRouter(prefix="/auth")
router.include_router(email_router)

__all__ = ["router"]
