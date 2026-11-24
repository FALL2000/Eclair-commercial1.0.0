"""Validateurs réutilisables du projet."""
import re

from fastapi import HTTPException

TENANT_SCHEMA_PATTERN = re.compile(r"^tenant_[a-z0-9_]{1,50}$")


def validate_tenant_schema(schema_name: str) -> str:
    """Vérifie qu'un nom de schéma tenant est sûr avant toute interpolation SQL.

    Format attendu : `tenant_` suivi de 1 à 50 caractères [a-z0-9_] (ex. `tenant_cm_dla_0042`).
    """
    if not isinstance(schema_name, str) or not TENANT_SCHEMA_PATTERN.fullmatch(schema_name):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_TENANT_SCHEMA",
                "message": "Nom de schéma d'entreprise invalide",
            },
        )
    return schema_name
