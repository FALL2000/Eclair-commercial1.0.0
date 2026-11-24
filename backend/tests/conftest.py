import os

# Variables d'environnement de test, positionnées avant tout import de l'application
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "cle-de-test-uniquement-pour-pytest-0123456789")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
