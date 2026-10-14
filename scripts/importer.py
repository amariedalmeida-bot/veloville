"""Import et fiabilisation des trois exports CSV dans PostgreSQL.

Lit data/stations.csv, data/trajets.csv et data/incidents.csv,
applique les règles de fiabilisation (api/services/fiabilisation.py),
charge les lignes valides dans l'ordre des dépendances (stations, puis trajets et incidents),
journalise les rejets et avertissements dans docs/rejets_et_avertissements.csv,
et garantit l'idempotence via des clauses ON CONFLICT DO NOTHING.

Usage : python scripts/importer.py [--dossier data]
"""

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Set

from dotenv import load_dotenv
import psycopg

RACINE_PROJET = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE_PROJET))

from api.services.fiabilisation import (
    fiabiliser_horodatage,
    fiabiliser_statut,
    valider_duree,
    valider_station_existante,
    valider_chronologie_incident,
    est_ligne_unique,
)


def get_db_connection_string() -> str:
    """Récupère l'URL de connexion et l'adapte pour psycopg3."""
    load_dotenv(RACINE_PROJET / ".env")
    url = os.getenv(
        "DATABASE_URL",
        "postgresql://veloville:veloville@localhost:5432/veloville",
    )
    if url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql+psycopg://", "postgresql://", 1)
    return url


class Journaliseur:
    """Enregistre les rejets et normalisations selon le format attendu."""

    def __init__(self, chemin_fichier: Path):
        self.chemin_fichier = chemin_fichier
        self.entrees: List[Dict[str, str]] = []

    def ajouter(
        self,
        fichier_source: str,
        identifiant: str,
        colonne: str,
        valeur: str,
        motif: str,
        decision: str,
    ) -> None:
        self.entrees.append({
            "fichier_source": fichier_source,
            "identifiant": identifiant,
            "colonne": colonne,
            "valeur": valeur,
            "motif": motif,
            "decision": decision,
        })

    def exporter(self) -> None:
        self.chemin_fichier.parent.mkdir(parents=True, exist_ok=True)
        champs = ["fichier_source", "identifiant", "colonne", "valeur", "motif", "decision"]
        with open(self.chemin_fichier, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=champs)
            writer.writeheader()
            writer.writerows(self.entrees)
        print(f"[Journal] {len(self.entrees)} événements écrits dans {self.chemin_fichier}")


def importer_stations(conn, chemin_csv: Path, journal: Journaliseur) -> Set[str]:
    print("\n--- 1. Importation des stations ---")
    stations_valides = set()
    lignes_a_inserer = []
    lignes_vues = set()

    with open(chemin_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for ligne in reader:
            s_id = ligne.get("station_id", "").strip()

            unique, motif = est_ligne_unique(ligne, lignes_vues)
            if not unique:
                journal.ajouter("stations.csv", s_id, "station_id", s_id, motif, "rejet")
                continue

            stations_valides.add(s_id)
            d_mise = ligne.get("date_mise_en_service", "").strip() or None

            lignes_a_inserer.append((
                s_id,
                ligne.get("nom", "").strip(),
                ligne.get("commune", "").strip(),
                int(ligne.get("capacite", 0)),
                float(ligne["latitude"]) if ligne.get("latitude") else None,
                float(ligne["longitude"]) if ligne.get("longitude") else None,
                d_mise,
            ))

    requete = """
        INSERT INTO station (station_id, nom, commune, capacite, latitude, longitude, date_mise_en_service)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (station_id) DO NOTHING;
    """
    with conn.cursor() as cur:
        cur.executemany(requete, lignes_a_inserer)
    conn.commit()

    print(f"Stations enregistrées : {len(lignes_a_inserer)}")
    return stations_valides


def importer_trajets(conn, chemin_csv: Path, stations_valides: Set[str], journal: Journaliseur) -> None:
    print("\n--- 2. Importation des trajets ---")
    trajets_a_inserer = []
    lignes_vues = set()
    ids_vus = set()

    with open(chemin_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for ligne in reader:
            t_id = ligne.get("trajet_id", "").strip()

            unique, motif_unique = est_ligne_unique(ligne, lignes_vues)
            if not unique:
                journal.ajouter("trajets.csv", t_id, "ligne", t_id, motif_unique, "rejet")
                continue

            if t_id in ids_vus:
                journal.ajouter("trajets.csv", t_id, "trajet_id", t_id, "Doublon clé primaire trajet_id", "rejet")
                continue
            ids_vus.add(t_id)

            s_dep = ligne.get("station_depart", "").strip()
            ok_dep, motif_dep = valider_station_existante(s_dep, stations_valides, est_facultatif=False)
            if not ok_dep:
                journal.ajouter("trajets.csv", t_id, "station_depart", s_dep, motif_dep, "rejet")
                continue

            s_arr = ligne.get("station_arrivee", "").strip()
            ok_arr, motif_arr = valider_station_existante(s_arr, stations_valides, est_facultatif=True)
            if not ok_arr:
                journal.ajouter("trajets.csv", t_id, "station_arrivee", s_arr, motif_arr, "rejet")
                continue

            h_dep_brut = ligne.get("depart_horodatage", "")
            h_dep_iso, avert_dep = fiabiliser_horodatage(h_dep_brut)
            if not h_dep_iso:
                journal.ajouter("trajets.csv", t_id, "depart_horodatage", h_dep_brut, avert_dep, "rejet")
                continue
            if avert_dep:
                journal.ajouter("trajets.csv", t_id, "depart_horodatage", h_dep_brut, avert_dep, "normalisation")

            duree_brute = ligne.get("duree_secondes", "")
            ok_duree, motif_duree = valider_duree(duree_brute)
            if not ok_duree:
                journal.ajouter("trajets.csv", t_id, "duree_secondes", str(duree_brute), motif_duree, "rejet")
                continue

            v_id = str(ligne.get("velo_id", "")).strip()
            type_u = ligne.get("type_usager", "").strip() or None
            u_ref = ligne.get("usager_ref", "").strip() or None

            trajets_a_inserer.append((
                t_id,
                v_id,
                h_dep_iso,
                s_dep,
                s_arr if s_arr else None,
                int(duree_brute),
                type_u,
                u_ref,
            ))

    requete = """
        INSERT INTO trajet (trajet_id, velo_id, depart_horodatage, station_depart, station_arrivee, duree_secondes, type_usager, usager_ref)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (trajet_id) DO NOTHING;
    """
    with conn.cursor() as cur:
        cur.executemany(requete, trajets_a_inserer)
    conn.commit()

    print(f"Trajets insérés : {len(trajets_a_inserer)}")


def importer_incidents(conn, chemin_csv: Path, stations_valides: Set[str], journal: Journaliseur) -> None:
    print("\n--- 3. Importation des incidents ---")
    incidents_a_inserer = []
    lignes_vues = set()
    ids_vus = set()

    with open(chemin_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for ligne in reader:
            inc_id = ligne.get("incident_id", "").strip()

            # 1. Doublon de ligne
            unique, motif_unique = est_ligne_unique(ligne, lignes_vues)
            if not unique:
                journal.ajouter("incidents.csv", inc_id, "ligne", inc_id, motif_unique, "rejet")
                continue

            # 2. Doublon d'identifiant primaire
            if inc_id in ids_vus:
                journal.ajouter("incidents.csv", inc_id, "incident_id", inc_id, "Doublon clé primaire incident_id", "rejet")
                continue
            ids_vus.add(inc_id)

            # 3. Validation station (facultative si l'incident porte sur un vélo)
            s_id = ligne.get("station_id", "").strip() or None
            ok_st, motif_st = valider_station_existante(s_id, stations_valides, est_facultatif=True)
            if not ok_st:
                journal.ajouter("incidents.csv", inc_id, "station_id", s_id, motif_st, "rejet")
                continue

            # 4. Normalisation statut (RG7)
            statut_brut = ligne.get("statut", "")
            statut_norm, avert_statut = fiabiliser_statut(statut_brut)
            if not statut_norm:
                journal.ajouter("incidents.csv", inc_id, "statut", statut_brut, avert_statut, "rejet")
                continue
            if avert_statut:
                journal.ajouter("incidents.csv", inc_id, "statut", statut_brut, avert_statut, "normalisation")

            # 5. Normalisation date de signalement
            d_sig_brut = ligne.get("date_signalement", "")
            d_sig_iso, avert_sig = fiabiliser_horodatage(d_sig_brut)
            if not d_sig_iso:
                journal.ajouter("incidents.csv", inc_id, "date_signalement", d_sig_brut, avert_sig, "rejet")
                continue
            if avert_sig:
                journal.ajouter("incidents.csv", inc_id, "date_signalement", d_sig_brut, avert_sig, "normalisation")

            # 6. Normalisation date de résolution
            d_res_brut = ligne.get("date_resolution", "").strip()
            d_res_iso = None
            if d_res_brut:
                d_res_iso, avert_res = fiabiliser_horodatage(d_res_brut)
                if not d_res_iso:
                    journal.ajouter("incidents.csv", inc_id, "date_resolution", d_res_brut, avert_res, "rejet")
                    continue
                if avert_res:
                    journal.ajouter("incidents.csv", inc_id, "date_resolution", d_res_brut, avert_res, "normalisation")

            # 7. Chronologie RG8
            ok_chrono, motif_chrono = valider_chronologie_incident(statut_norm, d_sig_iso, d_res_iso)
            if not ok_chrono:
                journal.ajouter("incidents.csv", inc_id, "date_resolution", str(d_res_brut), motif_chrono, "rejet")
                continue

            v_id = ligne.get("velo_id", "").strip() or None
            cible = ligne.get("cible", "").strip() or None
            tech = ligne.get("technicien", "").strip() or None

            incidents_a_inserer.append((
                inc_id,
                d_sig_iso,
                cible,
                v_id,
                s_id,
                ligne.get("type_incident", "").strip(),
                statut_norm,
                d_res_iso,
                tech,
            ))

    requete = """
        INSERT INTO incident (incident_id, date_signalement, cible, velo_id, station_id, type_incident, statut, date_resolution, technicien)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (incident_id) DO NOTHING;
    """
    with conn.cursor() as cur:
        cur.executemany(requete, incidents_a_inserer)
    conn.commit()

    print(f"Incidents insérés : {len(incidents_a_inserer)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import idempotent des exports CSV dans PostgreSQL.")
    parser.add_argument(
        "--dossier",
        type=str,
        default="data",
        help="Dossier contenant les fichiers CSV (défaut : data)",
    )
    args = parser.parse_args()

    chemin_data = RACINE_PROJET / args.dossier
    fichier_journal = RACINE_PROJET / "docs" / "rejets_et_avertissements.csv"

    journal = Journaliseur(fichier_journal)
    url_db = get_db_connection_string()

    try:
        with psycopg.connect(url_db) as conn:
            stations_connues = importer_stations(conn, chemin_data / "stations.csv", journal)
            importer_trajets(conn, chemin_data / "trajets.csv", stations_connues, journal)
            importer_incidents(conn, chemin_data / "incidents.csv", stations_connues, journal)
    except psycopg.OperationalError as e:
        print(f"\n[Erreur de connexion PostgreSQL] : {e}")
        print("Vérifiez la chaîne de connexion dans le fichier .env.")
        sys.exit(1)

    journal.exporter()
    print("\nImport terminé avec succès !")


if __name__ == "__main__":
    main()
