from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException

from config.settings import get_settings
from security.jwt_handler import create_tokens, decode_token
from security.password_hacher import hash_password, verify_password


def test_hash_et_verification_mot_de_passe():
    hashed = hash_password("MotDePasse!2026")
    assert hashed != "MotDePasse!2026"
    assert verify_password("MotDePasse!2026", hashed)
    assert not verify_password("mauvais", hashed)


def test_verification_hash_invalide_retourne_false():
    assert verify_password("x", "pas-un-hash-bcrypt") is False


def test_tokens_portent_le_schema_tenant():
    tokens = create_tokens("42", "tenant_cm_dla_0042")
    access = decode_token(tokens["access_token"])
    refresh = decode_token(tokens["refresh_token"])
    assert tokens["token_type"] == "bearer"
    assert access["sub"] == "42"
    assert access["tenant_schema"] == "tenant_cm_dla_0042"
    assert access["type"] == "access"
    assert refresh["type"] == "refresh"


def test_token_expire():
    settings = get_settings()
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    with pytest.raises(HTTPException) as exc:
        decode_token(expired)
    assert exc.value.status_code == 401
    assert exc.value.detail["error_code"] == "TOKEN_EXPIRED"


def test_token_invalide():
    with pytest.raises(HTTPException) as exc:
        decode_token("ceci.nest.pas.un.jwt")
    assert exc.value.detail["error_code"] == "INVALID_TOKEN"
