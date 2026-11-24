from sqlalchemy import text
from sqlmodel import Session

from utils.logger import get_logger

logger = get_logger()


class HealthService:
    def __init__(self, session: Session):
        self.session = session

    def check(self) -> dict:
        """Vérifie que l'API et la base de données répondent."""
        try:
            self.session.exec(text("SELECT 1"))
            database = "up"
        except Exception as e:
            logger.error(f"Base de données indisponible : {e}")
            database = "down"
        return {"status": "ok" if database == "up" else "degraded", "database": database}
