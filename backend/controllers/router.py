from fastapi import APIRouter

from controllers.systeme.health_controllers import router as health_router

router = APIRouter()


def include_api_routes() -> APIRouter:
    """Enregistre tous les sous-routeurs sur le routeur principal."""
    router.include_router(health_router, prefix="/health", tags=["systeme"])

    return router


include_api_routes()
