from .healthcheck import router as health_router
from .route import router
from .v1 import router as v1_router

router.include_router(v1_router)
router.include_router(health_router)

__all__ = ["router"]
