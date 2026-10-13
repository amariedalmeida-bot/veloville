"""Tests unitaires des règles de fiabilisation.

À compléter : un test par règle, cas nominal et cas de rejet.
"""
from datetime import datetime
from api.services.fiabilisation import (
    valider_station,
    valider_trajet,
    valider_incident,
    normaliser_chaine,
)


def test_normaliser_chaine():
    assert normaliser_chaine("  Lille  ") == "Lille"
    assert normaliser_chaine("   ") is None
    assert normaliser_chaine(None) is None


# RG1 : Station
def test_valider_station_nominal():
    ligne = {
        "station_id": "ST01",
        "nom": "Gare Lille Flandres",
        "commune": "Lille",
        "capacite": "20",
        "latitude": "50.636",
        "longitude": "3.070",
        "date_mise_en_service": "2024-01-01",
    }
    donnees, erreur = valider_station(ligne)
    assert erreur is None
    assert donnees["station_id"] == "ST01"
    assert donnees["capacite"] == 20


def test_valider_station_capacite_invalide():
    ligne = {
        "station_id": "ST01",
        "nom": "Gare",
        "commune": "Lille",
        "capacite": "0",
        "latitude": "50.636",
        "longitude": "3.070",
        "date_mise_en_service": "2024-01-01",
    }
    donnees, erreur = valider_station(ligne)
    assert donnees is None
    assert "Capacité négative ou nulle" in erreur


# RG2, RG3, RG4, RG5 : Trajet
def test_valider_trajet_nominal():
    stations_connues = {"ST01", "ST02"}
    ligne = {
        "trajet_id": "TR001",
        "velo_id": "V100",
        "station_depart": "ST01",
        "station_arrivee": "ST02",
        "duree_secondes": "600",
        "depart_horodatage": "2026-03-01T10:00:00",
        "type_usager": "abonne",
        "usager_ref": "USER_XYZ",
    }
    donnees, erreur = valider_trajet(ligne, stations_connues)
    assert erreur is None
    assert donnees["duree_secondes"] == 600
    assert donnees["usager_ref"] == "USER_XYZ"


def test_valider_trajet_station_inconnue_rejet():
    stations_connues = {"ST01"}
    ligne = {
        "trajet_id": "TR002",
        "velo_id": "V100",
        "station_depart": "ST99",
        "station_arrivee": "ST01",
        "duree_secondes": "300",
        "depart_horodatage": "2026-03-01T10:00:00",
        "type_usager": "abonne",
    }
    donnees, erreur = valider_trajet(ligne, stations_connues)
    assert donnees is None
    assert "Station de départ inconnue" in erreur


def test_valider_trajet_duree_invalide_rejet():
    stations_connues = {"ST01"}
    ligne = {
        "trajet_id": "TR003",
        "velo_id": "V100",
        "station_depart": "ST01",
        "station_arrivee": "",
        "duree_secondes": "-10",
        "depart_horodatage": "2026-03-01T10:00:00",
        "type_usager": "occasionnel",
    }
    donnees, erreur = valider_trajet(ligne, stations_connues)
    assert donnees is None
    assert "Durée de trajet négative ou nulle" in erreur


def test_valider_trajet_occasionnel_supprime_ref():
    stations_connues = {"ST01"}
    ligne = {
        "trajet_id": "TR004",
        "velo_id": "V100",
        "station_depart": "ST01",
        "station_arrivee": None,
        "duree_secondes": "400",
        "depart_horodatage": "2026-03-01T10:00:00",
        "type_usager": "occasionnel",
        "usager_ref": "PSEUDO_NE_PAS_GARDER",
    }
    donnees, erreur = valider_trajet(ligne, stations_connues)
    assert erreur is None
    assert donnees["usager_ref"] is None


# RG6, RG7, RG8 : Incident
def test_valider_incident_nominal():
    stations_connues = {"ST01"}
    ligne = {
        "incident_id": "INC01",
        "cible": "velo",
        "velo_id": "V100",
        "station_id": None,
        "type_incident": "crevaison",
        "statut": "en_cours",
        "date_signalement": "2026-03-01T08:00:00",
        "date_resolution": None,
        "technicien": "Alex",
    }
    donnees, erreur = valider_incident(ligne, stations_connues)
    assert erreur is None
    assert donnees["cible"] == "velo"
    assert donnees["statut"] == "en_cours"


def test_valider_incident_double_cible_rejet():
    stations_connues = {"ST01"}
    ligne = {
        "incident_id": "INC02",
        "cible": "velo",
        "velo_id": "V100",
        "station_id": "ST01",
        "type_incident": "crevaison",
        "statut": "ouvert",
        "date_signalement": "2026-03-01T08:00:00",
    }
    donnees, erreur = valider_incident(ligne, stations_connues)
    assert donnees is None
    assert "station_id doit être vide" in erreur


def test_valider_incident_dates_incoherentes_rejet():
    stations_connues = {"ST01"}
    ligne = {
        "incident_id": "INC03",
        "cible": "station",
        "velo_id": None,
        "station_id": "ST01",
        "type_incident": "borne_hs",
        "statut": "resolu",
        "date_signalement": "2026-03-02T12:00:00",
        "date_resolution": "2026-03-01T12:00:00",
    }
    donnees, erreur = valider_incident(ligne, stations_connues)
    assert donnees is None
    assert "antérieure à la date de signalement" in erreur