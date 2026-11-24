from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException

from config.settings import get_settings

settings = get_settings()


def create_tokens(user_id: str, tenant_schema: str) -> dict:
    """Génère un Access Token et un Refresh Token.

    Le schéma PostgreSQL de l'entreprise (`tenant_schema`) est porté par le token :
    c'est lui qui permet de router chaque requête vers les données de la bonne entreprise.
    """
    now = datetime.now(timezone.utc)
    base_payload = {"sub": str(user_id), "tenant_schema": tenant_schema, "iat": now}

    access_payload = {
        **base_payload,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    refresh_payload = {
        **base_payload,
        "exp": now + timedelta(days=settings.access_refresh_token_expire_days),
        "type": "refresh",
    }

    return {
        "access_token": jwt.encode(access_payload, settings.secret_key, algorithm=settings.algorithm),
        "refresh_token": jwt.encode(refresh_payload, settings.secret_key, algorithm=settings.algorithm),
        "token_type": "bearer",
    }


def decode_token(token: str) -> Optional[dict]:
    """Décode et valide un token JWT."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail={
                            "error_code": "TOKEN_EXPIRED", "message": "Token expired"})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail={
                            "error_code": "INVALID_TOKEN", "message": "Invalid token"})
