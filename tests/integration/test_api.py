"""Tests d'intégration de l'API avec TestClient.

À compléter : au moins /sante, /auth/login (OK et KO), une route protégée sans jeton
(401), PUT /incidents/{id}/statut avec le rôle direction (403).
"""
from datetime import date, datetime
import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.database import Base, get_db
from api.main import app
from api.models import Incident, Station, Trajet, Utilisateur
from api.securite import creer_jeton_jwt

# Moteur SQLite partagé entre threads pour TestClient
engine_test = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="module", autouse=True)
def setup_integration_db():
    """Initialise le schéma et injecte les données de référence."""
    Base.metadata.create_all(bind=engine_test)
    db = TestingSessionLocal()

    # Génération directe d'un hash bcrypt valide pour "password123"
    sel = bcrypt.gensalt()
    hash_valide = bcrypt.hashpw(b"password123", sel).decode("utf-8")

    u_exploitant = Utilisateur(
        username="exploitant_test",
        mot_de_passe_hash=hash_valide,
        role="exploitant",
    )
    u_direction = Utilisateur(
        username="direction_test",
        mot_de_passe_hash=hash_valide,
        role="direction",
    )
    db.add_all([u_exploitant, u_direction])

    st = Station(
        station_id="ST_TEST",
        nom="Station Test",
        commune="Lille",
        capacite=15,
        latitude=50.63,
        longitude=3.06,
        date_mise_en_service=date(2025, 1, 1),
    )
    inc = Incident(
        incident_id="INC_TEST",
        date_signalement=datetime(2026, 3, 1, 9, 0),
        cible="station",
        station_id="ST_TEST",
        type_incident="borne_hs",
        statut="ouvert",
    )
    tr = Trajet(
        trajet_id="TR_TEST",
        velo_id="V_TEST",
        depart_horodatage=datetime(2026, 3, 1, 10, 0),
        station_depart="ST_TEST",
        station_arrivee="ST_TEST",
        duree_secondes=500,
        type_usager="abonne",
        usager_ref="SECRET_REF",
    )
    db.add_all([st, inc, tr])
    db.commit()
    db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def client():
    return TestClient(app)


def test_sante(client):
    """GET /sante renvoie {'statut': 'ok'}."""
    reponse = client.get("/sante")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}


def test_login_succes(client):
    """POST /auth/login valide les identifiants et renvoie un jeton JWT."""
    reponse = client.post(
        "/auth/login",
        json={"username": "exploitant_test", "password": "password123"},
    )
    assert reponse.status_code == 200
    data = reponse.json()
    assert "access_token" in data
    assert data["role"] == "exploitant"


def test_login_echec(client):
    """POST /auth/login rejette les mauvais identifiants (401)."""
    reponse = client.post(
        "/auth/login",
        json={"username": "exploitant_test", "password": "mauvais_mot_de_passe"},
    )
    assert reponse.status_code == 401


def test_route_protegee_sans_jeton(client):
    """Accéder à une ressource protégée sans jeton renvoie 401 Unauthorized."""
    reponse = client.get("/stations")
    assert reponse.status_code == 401


def test_maj_statut_incident_interdit_direction(client):
    """Une tentative de mise à jour de statut par la direction renvoie 403 Forbidden."""
    jeton_direction = creer_jeton_jwt({"sub": "direction_test", "role": "direction"})
    headers = {"Authorization": f"Bearer {jeton_direction}"}

    reponse = client.put(
        "/incidents/INC_TEST/statut",
        headers=headers,
        json={"nouveau_statut": "en_cours"},
    )
    assert reponse.status_code == 403


def test_maj_statut_incident_succes_exploitant(client):
    """L'exploitant peut modifier le statut d'un incident (200)."""
    jeton_exploitant = creer_jeton_jwt({"sub": "exploitant_test", "role": "exploitant"})
    headers = {"Authorization": f"Bearer {jeton_exploitant}"}

    reponse = client.put(
        "/incidents/INC_TEST/statut",
        headers=headers,
        json={"nouveau_statut": "en_cours", "technicien": "Alex"},
    )
    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "en_cours"


def test_rgpd_masquage_usager_ref_pour_direction(client):
    """Vérifie le masquage de usager_ref pour le rôle direction."""
    jeton_direction = creer_jeton_jwt({"sub": "direction_test", "role": "direction"})
    reponse = client.get("/trajets", headers={"Authorization": f"Bearer {jeton_direction}"})
    assert reponse.status_code == 200
    trajets = reponse.json()["trajets"]
    assert len(trajets) > 0
    assert trajets[0]["usager_ref"] is None