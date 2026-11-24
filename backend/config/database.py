"""Connexion PostgreSQL et sessions multi-tenant (un schéma PostgreSQL par entreprise).

Le schéma `public` contient l'annuaire global (tenants, global_users).
Chaque entreprise possède son propre schéma `tenant_xxx`. Le schéma est appliqué avec
`SET LOCAL search_path` au début de CHAQUE transaction : un `SET` de session ne survivrait
pas au multiplexage de PgBouncer en mode transaction (cf. docs/SPECIFICATIONS_CONSOLIDEES.md §19.4).
"""
from sqlalchemy import event, text
from sqlmodel import Session, create_engine

from common.validators import validate_tenant_schema
from config.settings import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=280,
    echo=settings.db_echo,
)


def create_public_session() -> Session:
    """Session sur le schéma global `public` uniquement."""
    return Session(engine)


def create_tenant_session(schema_name: str) -> Session:
    """Session dont chaque transaction s'exécute dans le schéma de l'entreprise."""
    schema = validate_tenant_schema(schema_name)
    session = Session(engine)

    @event.listens_for(session, "after_begin")
    def _set_search_path(_session, _transaction, connection):
        # Le nom de schéma est validé par regex : l'interpolation est sûre.
        connection.execute(text(f'SET LOCAL search_path TO "{schema}", public'))

    return session
