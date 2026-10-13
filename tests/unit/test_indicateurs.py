"""Tests des fonctions de calcul des indicateurs.

À compléter : vérifier les agrégats sur un jeu de données connu.
"""
"""Tests des fonctions de calcul des indicateurs."""

from datetime import date, datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.database import Base
from api.models import Incident, Station, Trajet
from api.services.indicateurs import (
    activite_par_jour,
    incidents_par_statut,
    stations_actives,
)


@pytest.fixture
def session_test():
    """Jeu de test contrôlé en SQLite mémoire."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Stations
    s1 = Station(
        station_id="S01",
        nom="Gare",
        commune="Lille",
        capacite=20,
        latitude=50.63,
        longitude=3.07,
        date_mise_en_service=date(2024, 1, 1),
    )
    s2 = Station(
        station_id="S02",
        nom="Grand Place",
        commune="Lille",
        capacite=15,
        latitude=50.63,
        longitude=3.06,
        date_mise_en_service=date(2024, 1, 1),
    )
    session.add_all([s1, s2])

    # Trajets (3 trajets sur 2 jours)
    t1 = Trajet(
        trajet_id="T01",
        velo_id="V01",
        depart_horodatage=datetime(2026, 3, 1, 8, 30),
        station_depart="S01",
        station_arrivee="S02",
        duree_secondes=600,
        type_usager="abonne",
    )
    t2 = Trajet(
        trajet_id="T02",
        velo_id="V02",
        depart_horodatage=datetime(2026, 3, 1, 9, 0),
        station_depart="S01",
        station_arrivee="S01",
        duree_secondes=450,
        type_usager="occasionnel",
    )
    t3 = Trajet(
        trajet_id="T03",
        velo_id="V01",
        depart_horodatage=datetime(2026, 3, 2, 14, 0),
        station_depart="S02",
        station_arrivee="S01",
        duree_secondes=900,
        type_usager="abonne",
    )
    session.add_all([t1, t2, t3])

    # Incidents
    i1 = Incident(
        incident_id="INC01",
        date_signalement=datetime(2026, 3, 1, 10, 0),
        cible="velo",
        velo_id="V01",
        type_incident="crevaison",
        statut="ouvert",
    )
    i2 = Incident(
        incident_id="INC02",
        date_signalement=datetime(2026, 3, 1, 11, 0),
        date_resolution=datetime(2026, 3, 1, 13, 0),  # 2 heures
        cible="station",
        station_id="S01",
        type_incident="borne_hs",
        statut="resolu",
        technicien="Alex",
    )
    session.add_all([i1, i2])

    session.commit()
    yield session
    session.close()


def test_activite_par_jour_global(session_test):
    res = activite_par_jour(session_test)
    assert len(res) == 2
    assert res[0]["jour"] == "2026-03-01"
    assert res[0]["total_trajets"] == 2
    assert res[1]["jour"] == "2026-03-02"
    assert res[1]["total_trajets"] == 1


def test_activite_par_jour_filtre(session_test):
    res = activite_par_jour(session_test, date_debut=date(2026, 3, 2))
    assert len(res) == 1
    assert res[0]["jour"] == "2026-03-02"


def test_stations_actives(session_test):
    res = stations_actives(session_test, limite=2)
    assert len(res) == 2
    # S01 : 2 departs + 2 arrivees = 4 mouvements
    # S02 : 1 depart + 1 arrivee = 2 mouvements
    assert res[0]["station_id"] == "S01"
    assert res[0]["total_departs"] == 2
    assert res[0]["total_arrivees"] == 2
    assert res[0]["total_mouvements"] == 4


def test_incidents_par_statut(session_test):
    res = incidents_par_statut(session_test)
    assert "repartition" in res
    assert res["repartition"]["ouvert"] == 1
    assert res["repartition"]["resolu"] == 1
    assert res["delai_moyen_resolution_heures"] == 2.0