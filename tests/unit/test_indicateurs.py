"""Tests des fonctions de calcul des indicateurs.

À compléter : vérifier les agrégats sur un jeu de données connu.
"""

from datetime import date
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from api.schemas import ActiviteJour
from api.services.indicateurs import (
    activite_par_jour,
    stations_actives,
    incidents_par_statut,
)


@pytest.fixture
def session_test():
    """Crée une base SQLite en mémoire avec un jeu d'essai minimal pour les tests unitaires."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE station (
                station_id VARCHAR(50) PRIMARY KEY,
                nom VARCHAR(255),
                commune VARCHAR(100),
                capacite INT,
                latitude FLOAT,
                longitude FLOAT,
                date_mise_en_service DATE
            );
        """))
        conn.execute(text("""
            CREATE TABLE trajet (
                trajet_id VARCHAR(50) PRIMARY KEY,
                velo_id VARCHAR(50),
                depart_horodatage TEXT,
                station_depart VARCHAR(50),
                station_arrivee VARCHAR(50),
                duree_secondes INT,
                type_usager VARCHAR(50),
                usager_ref VARCHAR(100)
            );
        """))
        conn.execute(text("""
            CREATE TABLE incident (
                incident_id VARCHAR(50) PRIMARY KEY,
                date_signalement TEXT,
                cible VARCHAR(20),
                velo_id VARCHAR(50),
                station_id VARCHAR(50),
                type_incident VARCHAR(100),
                statut VARCHAR(20),
                date_resolution TEXT,
                technicien VARCHAR(100)
            );
        """))

        conn.execute(text("""
            INSERT INTO station (station_id, nom, commune, capacite) VALUES
            ('S1', 'Gare Centrale', 'Lille', 20),
            ('S2', 'Grand Place', 'Lille', 15);
        """))
        conn.execute(text("""
            INSERT INTO trajet (trajet_id, depart_horodatage, station_depart, station_arrivee, duree_secondes) VALUES
            ('T1', '2026-08-24 08:00:00', 'S1', 'S2', 600),
            ('T2', '2026-08-24 10:00:00', 'S1', 'S2', 700),
            ('T3', '2026-08-25 12:00:00', 'S2', 'S1', 800);
        """))
        conn.execute(text("""
            INSERT INTO incident (incident_id, date_signalement, statut, date_resolution) VALUES
            ('I1', '2026-08-20 10:00:00', 'ouvert', NULL),
            ('I2', '2026-08-21 10:00:00', 'en_cours', NULL),
            ('I3', '2026-08-22 10:00:00', 'resolu', '2026-08-23 10:00:00');
        """))
        conn.commit()

    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_activite_par_jour_sans_filtre(session_test):
    res = activite_par_jour(session_test)
    assert len(res) == 2
    assert res[0]["jour"] == "2026-08-24"
    assert res[0]["nb_trajets"] == 2
    assert res[1]["jour"] == "2026-08-25"
    assert res[1]["nb_trajets"] == 1


def test_activite_par_jour_reponse_serialise_date(session_test):
    ligne = activite_par_jour(session_test)[0]
    reponse = ActiviteJour.model_validate(ligne)

    assert reponse.date == date(2026, 8, 24)
    assert reponse.model_dump(mode="json")["date"] == "2026-08-24"


def test_activite_par_jour_avec_filtre(session_test):
    res = activite_par_jour(
        session_test,
        date_debut=date(2026, 8, 25),
        date_fin=date(2026, 8, 25),
    )
    assert len(res) == 1
    assert res[0]["jour"] == "2026-08-25"
    assert res[0]["nb_trajets"] == 1


def test_stations_actives(session_test):
    res = stations_actives(session_test, limite=2)
    assert len(res) == 2
    assert res[0]["station_id"] == "S1"
    assert res[0]["nb_departs"] == 2
    assert res[0]["nb_arrivees"] == 1
    assert res[0]["total_trajets"] == 3


def test_incidents_par_statut(session_test):
    res = incidents_par_statut(session_test)
    statuts = {row["statut"]: row for row in res}

    assert "ouvert" in statuts
    assert statuts["ouvert"]["nb_incidents"] == 1
    assert statuts["ouvert"]["delai_moyen_heures"] is None

    assert "resolu" in statuts
    assert statuts["resolu"]["nb_incidents"] == 1
    assert statuts["resolu"]["delai_moyen_heures"] == 24.0