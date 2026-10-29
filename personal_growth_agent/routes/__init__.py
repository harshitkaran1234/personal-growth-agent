from .healthcheck import router as health_router
from .route import router

router.include_router(health_router)

__all__ = ["router"]
