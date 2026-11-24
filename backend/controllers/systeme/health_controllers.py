from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

from common.dependencies import get_db
from services.systeme.health_service import HealthService

router = APIRouter()


def get_health_service(db: Session = Depends(get_db)):
    return HealthService(db)


@router.get(
    "",
    summary="Vérifier l'état de l'API et de la base de données",
    status_code=200,
)
def health(health_service: Annotated[HealthService, Depends(get_health_service)]):
    result = health_service.check()
    return JSONResponse(status_code=200 if result["database"] == "up" else 503, content=result)
