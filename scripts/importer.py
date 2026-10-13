"""Import et fiabilisation des trois exports CSV dans PostgreSQL.

À compléter : lire data/stations.csv, data/trajets.csv et data/incidents.csv,
appliquer les règles de fiabilisation (api/services/fiabilisation.py),
charger les lignes valides, journaliser les rejets et les avertissements.
Le script doit être idempotent : deux exécutions successives laissent la
base dans le même état.

Usage prévu : python scripts/importer.py [--dossier data]
"""


import argparse
import csv
import logging
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Permet l'import du module api depuis la racine
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.services.fiabilisation import (
    valider_incident,
    valider_station,
    valider_trajet,
)

load_dotenv()

LOG_FILE = Path("data/rejets.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)


def get_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL non configuré dans .env")
    return create_engine(db_url)


def importer_stations(conn, dossier: Path) -> set[str]:
    fichier = dossier / "stations.csv"
    stations_valides = []
    ids_connus = set()

    with open(fichier, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for num, ligne in enumerate(reader, start=2):
            data, err = valider_station(ligne)
            if err:
                logging.warning("Station rejetée (ligne %d) : %s | %s", num, err, ligne)
                continue
            if data["station_id"] in ids_connus:
                logging.warning("Station doublon rejetée (ligne %d) : %s", num, data["station_id"])
                continue
            ids_connus.add(data["station_id"])
            stations_valides.append(data)

    query = text(
        """
        INSERT INTO station (station_id, nom, commune, capacite, latitude, longitude, date_mise_en_service)
        VALUES (:station_id, :nom, :commune, :capacite, :latitude, :longitude, :date_mise_en_service)
        ON CONFLICT (station_id) DO UPDATE SET
            nom = EXCLUDED.nom,
            commune = EXCLUDED.commune,
            capacite = EXCLUDED.capacite,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            date_mise_en_service = EXCLUDED.date_mise_en_service;
        """
    )
    for st in stations_valides:
        conn.execute(query, st)

    print(f"Stations importées/mises à jour : {len(stations_valides)}")
    return ids_connus


def importer_trajets(conn, dossier: Path, stations_connues: set[str]):
    fichier = dossier / "trajets.csv"
    trajets_valides = []
    ids_connus = set()

    with open(fichier, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for num, ligne in enumerate(reader, start=2):
            data, err = valider_trajet(ligne, stations_connues)
            if err:
                logging.warning("Trajet rejeté (ligne %d) : %s | %s", num, err, ligne)
                continue
            if data["trajet_id"] in ids_connus:
                logging.warning("Trajet doublon rejeté (ligne %d) : %s", num, data["trajet_id"])
                continue
            ids_connus.add(data["trajet_id"])
            trajets_valides.append(data)

    query = text(
        """
        INSERT INTO trajet (trajet_id, velo_id, depart_horodatage, station_depart, station_arrivee, duree_secondes, type_usager, usager_ref)
        VALUES (:trajet_id, :velo_id, :depart_horodatage, :station_depart, :station_arrivee, :duree_secondes, :type_usager, :usager_ref)
        ON CONFLICT (trajet_id) DO UPDATE SET
            velo_id = EXCLUDED.velo_id,
            depart_horodatage = EXCLUDED.depart_horodatage,
            station_depart = EXCLUDED.station_depart,
            station_arrivee = EXCLUDED.station_arrivee,
            duree_secondes = EXCLUDED.duree_secondes,
            type_usager = EXCLUDED.type_usager,
            usager_ref = EXCLUDED.usager_ref;
        """
    )
    for tr in trajets_valides:
        conn.execute(query, tr)

    print(f"Trajets importés/mis à jour : {len(trajets_valides)}")


def importer_incidents(conn, dossier: Path, stations_connues: set[str]):
    fichier = dossier / "incidents.csv"
    incidents_valides = []
    ids_connus = set()

    with open(fichier, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for num, ligne in enumerate(reader, start=2):
            data, err = valider_incident(ligne, stations_connues)
            if err:
                logging.warning("Incident rejeté (ligne %d) : %s | %s", num, err, ligne)
                continue
            if data["incident_id"] in ids_connus:
                logging.warning("Incident doublon rejeté (ligne %d) : %s", num, data["incident_id"])
                continue
            ids_connus.add(data["incident_id"])
            incidents_valides.append(data)

    query = text(
        """
        INSERT INTO incident (incident_id, date_signalement, cible, velo_id, station_id, type_incident, statut, date_resolution, technicien)
        VALUES (:incident_id, :date_signalement, :cible, :velo_id, :station_id, :type_incident, :statut, :date_resolution, :technicien)
        ON CONFLICT (incident_id) DO UPDATE SET
            date_signalement = EXCLUDED.date_signalement,
            cible = EXCLUDED.cible,
            velo_id = EXCLUDED.velo_id,
            station_id = EXCLUDED.station_id,
            type_incident = EXCLUDED.type_incident,
            statut = EXCLUDED.statut,
            date_resolution = EXCLUDED.date_resolution,
            technicien = EXCLUDED.technicien;
        """
    )
    for inc in incidents_valides:
        conn.execute(query, inc)

    print(f"Incidents importés/mis à jour : {len(incidents_valides)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import et fiabilisation des exports CSV")
    parser.add_argument("--dossier", default="data", help="Dossier contenant les fichiers CSV")
    args = parser.parse_args()

    dossier = Path(args.dossier)
    if not dossier.exists():
        print(f"Erreur : le dossier {dossier} est introuvable.")
        sys.exit(1)

    engine = get_engine()
    with engine.begin() as conn:
        stations_connues = importer_stations(conn, dossier)
        importer_trajets(conn, dossier, stations_connues)
        importer_incidents(conn, dossier, stations_connues)

    print("Import terminé avec succès. Consultez data/rejets.log pour le détail des rejets.")


if __name__ == "__main__":
    main()