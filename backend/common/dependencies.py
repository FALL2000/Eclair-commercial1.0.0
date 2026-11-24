"""Fichier de dépendances pour les routes et fonctions du projet."""
from collections.abc import Generator

from sqlmodel import Session

from config.database import create_public_session


def get_db() -> Generator[Session, None, None]:
    """Ouvre une session sur le schéma global `public`.

    Les routes métier utiliseront une dépendance `get_tenant_db` qui lira le schéma
    de l'entreprise dans le JWT puis appellera `config.database.create_tenant_session`.
    """
    with create_public_session() as session:
        yield session
