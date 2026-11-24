from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import get_settings
from controllers.router import router as api_router
from utils.logger import get_logger

logger = get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Gère le cycle de vie de l'application (démarrage puis arrêt du serveur)."""
    logger.info("Application FastAPI démarrée (lifespan startup)")
    yield
    logger.info("Application FastAPI arrêtée (lifespan shutdown)")


def init_api() -> FastAPI:
    logger.info("L'application démarre")

    application = FastAPI(title="Eclair Commercial API", lifespan=lifespan)

    application.include_router(api_router, prefix=settings.api_prefix)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return application


app = init_api()


@app.get("/ping")
def ping_route():
    """Route pour vérifier que FastAPI fonctionne"""
    return {"status": "success", "message": "Le serveur FastAPI tourne !"}


@app.exception_handler(RequestValidationError)
async def validation_error_handler_app(_request: Request, exceptions: RequestValidationError):
    """Gestion des erreurs retournées par les validateurs pydantic"""
    error_messages = [
        {"location": error["loc"], "message": error["msg"]}
        for error in exceptions.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": error_messages})


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host_ip,
        port=8000,
        reload=settings.debug,
    )
