from fastapi import Query

from common.dependencies import get_db
from main import app


class _SessionOk:
    def exec(self, _statement):
        return None


class _SessionKo:
    def exec(self, _statement):
        raise RuntimeError("connexion refusée")


@app.get("/_test/validation")
def _route_validation(nombre: int = Query(...)):
    return {"nombre": nombre}


def test_ping(client):
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_health_base_disponible(client):
    app.dependency_overrides[get_db] = lambda: _SessionOk()
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_health_base_indisponible(client):
    app.dependency_overrides[get_db] = lambda: _SessionKo()
    response = client.get("/api/v1/health")
    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "down"}


def test_erreur_validation_retourne_400(client):
    response = client.get("/_test/validation", params={"nombre": "abc"})
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail[0]["location"] == ["query", "nombre"]
