"""Tests d'intégration de l'API avec TestClient.

À compléter : au moins /sante, /auth/login (OK et KO), une route protégée sans jeton
(401), PUT /incidents/{id}/statut avec le rôle direction (403).
"""
"""Tests d'intégration de l'API VéloVille avec TestClient (codes 200, 401, 403, 404, 422)."""

import pytest
from fastapi.testclient import TestClient


def test_sante(client: TestClient):
    """Vérifie la route GET /sante -> statut 200 et 'ok'."""
    reponse = client.get("/sante")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}


def test_login_succes(client: TestClient):
    """Vérifie l'authentification avec identifiants valides."""
    payload = {"username": "exploitant01", "password": "Formation2026!"}
    reponse = client.post("/auth/login", json=payload)
    assert reponse.status_code == 200
    data = reponse.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_echec_401(client: TestClient):
    """Vérifie le rejet avec mauvais mot de passe (code 401)."""
    payload = {"username": "exploitant01", "password": "mauvais_mot_de_passe"}
    reponse = client.post("/auth/login", json=payload)
    assert reponse.status_code == 401
    assert reponse.json()["detail"] == "Identifiants incorrects"

def test_route_protegee_sans_jeton_401(client: TestClient):
    """Accéder à une route protégée sans token renvoie 401."""
    reponse = client.get("/stations")
    assert reponse.status_code == 401


def test_route_protegee_avec_jeton_valide_200(client: TestClient, headers_direction: dict):
    """Accéder à une route protégée avec un token valide renvoie 200."""
    reponse = client.get("/stations", headers=headers_direction)
    assert reponse.status_code == 200
    data = reponse.json()
    assert "total" in data
    assert "items" in data


def test_station_introuvable_404(client: TestClient, headers_direction: dict):
    """Demander une station inexistante renvoie 404."""
    reponse = client.get("/stations/STATION_INCONNUE_9999", headers=headers_direction)
    assert reponse.status_code == 404


def test_pagination_invalide_422(client: TestClient, headers_direction: dict):
    """Passer un numéro de page < 1 doit renvoyer 422 Unprocessable Entity."""
    reponse = client.get("/stations?page=0", headers=headers_direction)
    assert reponse.status_code == 422


def test_modification_statut_incident_interdite_direction_403(
    client: TestClient, headers_direction: dict
):
    """Un utilisateur 'direction' ne peut pas modifier un incident (code 403)."""
    payload = {"statut": "en_cours"}
    reponse = client.put(
        "/incidents/INC-0001/statut",
        json=payload,
        headers=headers_direction,
    )
    assert reponse.status_code == 403


def test_modification_statut_incident_autorisee_exploitant_200(
    client: TestClient, headers_exploitant: dict, db_session
):
    """Un exploitant peut modifier le statut d'un incident existant."""
    from api.models import Incident

    premier_incident = db_session.query(Incident).first()
    assert premier_incident is not None, "Aucun incident en base pour exécuter le test"

    payload = {"statut": "resolu"}
    reponse = client.put(
        f"/incidents/{premier_incident.incident_id}/statut",
        json=payload,
        headers=headers_exploitant,
    )
    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "resolu"