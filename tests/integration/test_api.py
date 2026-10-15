"""Tests d'intégration de l'API avec TestClient.

À compléter : au moins /sante, /auth/login (OK et KO), une route protégée sans jeton
(401), PUT /incidents/{id}/statut avec le rôle direction (403).
"""
"""Tests d'intégration de l'API VéloVille avec TestClient (codes 200, 401, 403, 404, 422)."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from api.database import Base, get_db
from api.main import app
from api.models import Incident, Utilisateur


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
    assert "page" in data
    assert "taille_page" in data
    assert "resultats" in data
    assert "items" not in data
    assert "pages" not in data


def test_indicateur_stations_actives_retourne_departs_arrivees_et_total(
    client: TestClient, headers_direction: dict
):
    """L'API conserve les métriques calculées pour les stations actives."""
    reponse = client.get(
        "/indicateurs/stations-actives?limite=1",
        headers=headers_direction,
    )

    assert reponse.status_code == 200
    station = reponse.json()[0]
    assert station["nb_departs"] >= 0
    assert station["nb_arrivees"] >= 0
    assert station["total_trajets"] == station["nb_departs"] + station["nb_arrivees"]


def test_filtre_stations_par_commune(client: TestClient, headers_direction: dict):
    """Les communes disponibles sont listées et le filtre ne renvoie que la commune choisie."""
    communes = client.get("/stations/communes", headers=headers_direction)
    assert communes.status_code == 200
    assert "Lille" in communes.json()

    stations = client.get(
        "/stations",
        params={"commune": "Lille", "taille_page": 100},
        headers=headers_direction,
    )
    assert stations.status_code == 200
    assert stations.json()["total"] > 0
    assert all(station["commune"] == "Lille" for station in stations.json()["resultats"])


def test_lister_trajets_serialize_horodatages(client: TestClient, headers_direction: dict):
    """L'API sérialise les horodatages des trajets en ISO 8601."""
    reponse = client.get("/trajets?taille_page=5", headers=headers_direction)
    assert reponse.status_code == 200
    horodatage = reponse.json()["resultats"][0]["depart_horodatage"]
    assert "T" in horodatage


def test_filtre_trajets_par_periode_inclut_date_fin(
    client: TestClient, headers_direction: dict
):
    """La borne date_fin inclut les trajets de toute la journée indiquée."""
    reponse = client.get(
        "/trajets",
        params={
            "date_debut": "2026-08-24",
            "date_fin": "2026-08-24",
            "taille_page": 100,
        },
        headers=headers_direction,
    )

    assert reponse.status_code == 200
    assert reponse.json()["total"] > 0
    assert all(
        item["depart_horodatage"].startswith("2026-08-24")
        for item in reponse.json()["resultats"]
    )


def test_filtre_trajets_par_station_depart_ou_arrivee(
    client: TestClient, headers_direction: dict
):
    """Le filtre station inclut les trajets où la station est au départ ou à l'arrivée."""
    reponse = client.get(
        "/trajets",
        params={"station": "S001", "taille_page": 100},
        headers=headers_direction,
    )

    assert reponse.status_code == 200
    trajets = reponse.json()["resultats"]
    assert reponse.json()["total"] == len(trajets)
    assert any(trajet["station_depart"] == "S001" for trajet in trajets)
    assert any(trajet["station_arrivee"] == "S001" for trajet in trajets)
    assert all(
        trajet["station_depart"] == "S001" or trajet["station_arrivee"] == "S001"
        for trajet in trajets
    )


def test_lister_trajets_ordre_chronologique_croissant(
    client: TestClient, headers_direction: dict
):
    """Les trajets sont retournés du plus ancien au plus récent."""
    reponse = client.get("/trajets?taille_page=20", headers=headers_direction)

    assert reponse.status_code == 200
    horodatages = [
        trajet["depart_horodatage"] for trajet in reponse.json()["resultats"]
    ]
    assert horodatages == sorted(horodatages)


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
    client: TestClient, headers_exploitant: dict
):
    """La mise à jour d'un incident s'exécute dans une base isolée."""
    moteur = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(moteur)

    try:
        with Session(moteur) as session_test:
            date_signalement = datetime.now() - timedelta(days=1)
            session_test.add_all(
                [
                    Utilisateur(
                        username="exploitant01",
                        mot_de_passe_hash="hachage-inutilise",
                        role="exploitant",
                    ),
                    Incident(
                        incident_id="INC-TEST",
                        date_signalement=date_signalement,
                        cible="velo",
                        velo_id="V-TEST",
                        statut="ouvert",
                    ),
                ]
            )
            session_test.commit()

            def remplacer_session_db():
                yield session_test

            dependance_precedente = app.dependency_overrides.get(get_db)
            app.dependency_overrides[get_db] = remplacer_session_db
            try:
                reponse = client.put(
                    "/incidents/INC-TEST/statut",
                    json={"statut": "resolu"},
                    headers=headers_exploitant,
                )
            finally:
                if dependance_precedente is None:
                    app.dependency_overrides.pop(get_db, None)
                else:
                    app.dependency_overrides[get_db] = dependance_precedente

            assert reponse.status_code == 200
            assert reponse.json()["statut"] == "resolu"
            assert reponse.json()["date_resolution"] is not None
            incident = session_test.query(Incident).filter_by(incident_id="INC-TEST").one()
            session_test.refresh(incident)
            assert incident.date_resolution >= incident.date_signalement
    finally:
        moteur.dispose()