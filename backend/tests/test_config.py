import os
import socket

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from common.dependencies import get_db
from common.validators import validate_tenant_schema
from config.database import create_tenant_session, engine
from config.settings import Settings, get_settings


@pytest.mark.parametrize("schema", ["tenant_0042", "tenant_cm_dla_0042", "tenant_a"])
def test_schema_tenant_valide(schema):
    assert validate_tenant_schema(schema) == schema


@pytest.mark.parametrize(
    "schema",
    ["public", "tenant_", "Tenant_01", "tenant_01; DROP TABLE x", 'tenant_01"', "tenant_" + "a" * 51, None],
)
def test_schema_tenant_invalide(schema):
    with pytest.raises(HTTPException) as exc:
        validate_tenant_schema(schema)
    assert exc.value.status_code == 400


def test_session_tenant_refuse_un_schema_invalide():
    with pytest.raises(HTTPException):
        create_tenant_session("public")


def test_settings_url_et_origines():
    settings = Settings(db_user="u", db_password="p", db_host="h", db_port=1, db_name="d",
                        origins_cors="http://a.cm, http://b.cm")
    assert settings.database_url == "postgresql+psycopg://u:p@h:1/d"
    assert settings.origins == ["http://a.cm", "http://b.cm"]
    assert Settings(origins_cors="").origins == ["*"]


def test_get_db_ouvre_une_session():
    generator = get_db()
    session = next(generator)
    assert session.bind is engine
    generator.close()


def _postgres_disponible() -> bool:
    """Sonde réseau rapide (1 s) pour ne pas bloquer la collecte des tests en local."""
    settings = get_settings()
    try:
        with socket.create_connection((settings.db_host, settings.db_port), timeout=1):
            return True
    except OSError:
        return False


@pytest.mark.skipif(
    not os.getenv("CI") and not _postgres_disponible(),
    reason="PostgreSQL indisponible en local (toujours exécuté en CI)",
)
def test_session_tenant_applique_search_path():
    with engine.begin() as connection:
        connection.execute(text('CREATE SCHEMA IF NOT EXISTS "tenant_test_ci"'))
    with create_tenant_session("tenant_test_ci") as session:
        search_path = session.exec(text("SHOW search_path")).one()[0]
    assert search_path.startswith('"tenant_test_ci"') or search_path.startswith("tenant_test_ci")
    with engine.begin() as connection:
        connection.execute(text('DROP SCHEMA IF EXISTS "tenant_test_ci" CASCADE'))
