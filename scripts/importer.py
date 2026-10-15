"""Script d'ingestion et de fiabilisation des données VéloVille (Point 8).

Ordre d'insertion :
1. stations
2. trajets
3. incidents

Utilise obligatoirement les fonctions pures de api/services/fiabilisation.py.
Produit le journal d'audit dans docs/rapport_import.csv.
Vérifie la réconciliation : importées + rejetées + doublons = total CSV.
Garantit l'idempotence des insertions.
"""
import csv
import os
from pathlib import Path
from typing import Any, Dict, List, Set

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from api.services.fiabilisation import (
    est_ligne_unique,
    fiabiliser_cible_incident,
    fiabiliser_horodatage,
    fiabiliser_statut,
    valider_chronologie_incident,
    valider_capacite,
    valider_duree,
    valider_station_existante,
)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"
DOCS_DIR.mkdir(exist_ok=True)
RAPPORT_CSV = DOCS_DIR / "rapport_import.csv"

# Connexion SQLite locale par défaut si DATABASE_URL n'est pas configuré
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'veloville.db'}")

journal_audit: List[Dict[str, str]] = []


def journaliser(
    fichier: str,
    identifiant: str,
    colonne: str,
    valeur: Any,
    motif: str,
    decision: str,
) -> None:
    """Consigne un événement dans le journal d'audit."""
    journal_audit.append(
        {
            "fichier_source": fichier,
            "identifiant": str(identifiant or "INCONNU"),
            "colonne": colonne,
            "valeur": str(valeur if valeur is not None else ""),
            "motif": motif,
            "decision": decision,
        }
    )


def importer_stations(session: Session) -> Set[str]:
    """Importe les stations et retourne l'ensemble des identifiants valides."""
    fichier = "stations.csv"
    path = DATA_DIR / fichier
    if not path.exists():
        print(f"Fichier introuvable : {path}")
        return set()

    total_csv = 0
    nb_doublons = 0
    nb_rejets = 0
    empreintes_vues: Set[tuple] = set()
    stations_valides: Dict[str, Dict[str, Any]] = {}

    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for ligne in reader:
            total_csv += 1
            s_id = (ligne.get("station_id") or "").strip()

            # 1. Doublon strict
            is_unique, motif_d = est_ligne_unique(ligne, empreintes_vues)
            if not is_unique:
                nb_doublons += 1
                journaliser(fichier, s_id, "ligne", "", motif_d, "rejet")
                continue

            # 2. Identifiant obligatoire
            if not s_id or s_id in stations_valides:
                nb_rejets += 1
                journaliser(fichier, s_id, "station_id", s_id, "Identifiant vide ou dupliqué", "rejet")
                continue

            # 3. Capacité (RG1 : entier strictement positif)
            capacite_valide, capacite, motif_capacite = valider_capacite(ligne.get("capacite"))
            if not capacite_valide:
                nb_rejets += 1
                journaliser(fichier, s_id, "capacite", ligne.get("capacite"), motif_capacite, "rejet")
                continue

            # 4. Coordonnées GPS
            try:
                lat = float(ligne.get("latitude", 0.0))
                lon = float(ligne.get("longitude", 0.0))
            except (ValueError, TypeError):
                lat, lon = 0.0, 0.0
                journaliser(fichier, s_id, "coordonnees", "", "Coordonnées invalides", "normalisation")

            # 5. Date de mise en service
            date_mes, motif_mes = fiabiliser_horodatage(ligne.get("date_mise_en_service"))
            if motif_mes and date_mes:
                journaliser(fichier, s_id, "date_mise_en_service", ligne.get("date_mise_en_service"), motif_mes, "normalisation")

            stations_valides[s_id] = {
                "station_id": s_id,
                "nom": (ligne.get("nom") or "").strip(),
                "commune": (ligne.get("commune") or "").strip(),
                "capacite": capacite,
                "latitude": lat,
                "longitude": lon,
                "date_mise_en_service": date_mes,
            }

    # Insertion idempotente
    for st in stations_valides.values():
        stmt = text("""
            INSERT INTO station (station_id, nom, commune, capacite, latitude, longitude, date_mise_en_service)
            VALUES (:station_id, :nom, :commune, :capacite, :latitude, :longitude, :date_mise_en_service)
            ON CONFLICT (station_id) DO UPDATE SET
                nom = EXCLUDED.nom,
                commune = EXCLUDED.commune,
                capacite = EXCLUDED.capacite,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                date_mise_en_service = EXCLUDED.date_mise_en_service;
        """)
        session.execute(stmt, st)

    session.commit()
    nb_import = len(stations_valides)
    print(f"[{fichier}] Total CSV: {total_csv} = Importées: {nb_import} + Rejetées: {nb_rejets} + Doublons: {nb_doublons}")
    assert total_csv == nb_import + nb_rejets + nb_doublons, f"Équation non respectée pour {fichier}"
    return set(stations_valides.keys())


def importer_trajets(session: Session, stations_connues: Set[str]) -> None:
    """Importe les trajets avec intégrité référentielle et durée strictement positive."""
    fichier = "trajets.csv"
    path = DATA_DIR / fichier
    if not path.exists():
        print(f"Fichier introuvable : {path}")
        return

    total_csv = 0
    nb_doublons = 0
    nb_rejets = 0
    empreintes_vues: Set[tuple] = set()
    trajets_valides: Dict[str, Dict[str, Any]] = {}

    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for ligne in reader:
            total_csv += 1
            t_id = (ligne.get("trajet_id") or "").strip()

            # 1. Doublon strict
            is_unique, motif_d = est_ligne_unique(ligne, empreintes_vues)
            if not is_unique:
                nb_doublons += 1
                journaliser(fichier, t_id, "ligne", "", motif_d, "rejet")
                continue

            if not t_id or t_id in trajets_valides:
                nb_rejets += 1
                journaliser(fichier, t_id, "trajet_id", t_id, "Identifiant trajet manquant ou dupliqué", "rejet")
                continue

            # 2. Validation durée (RG4 : durée > 0 obligatoire)
            duree_valide, motif_duree = valider_duree(ligne.get("duree_secondes"))
            if not duree_valide:
                nb_rejets += 1
                journaliser(fichier, t_id, "duree_secondes", ligne.get("duree_secondes"), motif_duree, "rejet")
                continue

            # 3. Validation station de départ (RG2/RG3 obligatoire)
            st_dep = (ligne.get("station_depart") or "").strip()
            dep_valide, motif_dep = valider_station_existante(st_dep, stations_connues, est_facultatif=False)
            if not dep_valide:
                nb_rejets += 1
                journaliser(fichier, t_id, "station_depart", st_dep, motif_dep, "rejet")
                continue

            # 4. Validation station d'arrivée (facultative si trajet en cours, mais si fournie doit exister)
            st_arr = (ligne.get("station_arrivee") or "").strip()
            arr_valide, motif_arr = valider_station_existante(st_arr, stations_connues, est_facultatif=True)
            if not arr_valide:
                nb_rejets += 1
                journaliser(fichier, t_id, "station_arrivee", st_arr, motif_arr, "rejet")
                continue

            # 5. Fiabilisation horodatage
            date_dep, motif_dep_h = fiabiliser_horodatage(ligne.get("depart_horodatage"))
            if not date_dep:
                nb_rejets += 1
                journaliser(fichier, t_id, "depart_horodatage", ligne.get("depart_horodatage"), motif_dep_h, "rejet")
                continue
            if motif_dep_h:
                journaliser(fichier, t_id, "depart_horodatage", ligne.get("depart_horodatage"), motif_dep_h, "normalisation")

            trajets_valides[t_id] = {
                "trajet_id": t_id,
                "velo_id": (ligne.get("velo_id") or "").strip(),
                "depart_horodatage": date_dep,
                "station_depart": st_dep,
                "station_arrivee": st_arr or None,
                "duree_secondes": int(ligne.get("duree_secondes")),
                "type_usager": (ligne.get("type_usager") or "").strip(),
                "usager_ref": (ligne.get("usager_ref") or "").strip(),
            }

    # Insertion idempotente
    for tr in trajets_valides.values():
        stmt = text("""
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
        """)
        session.execute(stmt, tr)

    session.commit()
    nb_import = len(trajets_valides)
    print(f"[{fichier}] Total CSV: {total_csv} = Importées: {nb_import} + Rejetées: {nb_rejets} + Doublons: {nb_doublons}")
    assert total_csv == nb_import + nb_rejets + nb_doublons, f"Équation non respectée pour {fichier}"


def importer_incidents(session: Session, stations_connues: Set[str]) -> None:
    """Importe les incidents avec statut RG7 et cohérence chronologique RG8."""
    fichier = "incidents.csv"
    path = DATA_DIR / fichier
    if not path.exists():
        print(f"Fichier introuvable : {path}")
        return

    total_csv = 0
    nb_doublons = 0
    nb_rejets = 0
    empreintes_vues: Set[tuple] = set()
    incidents_valides: Dict[str, Dict[str, Any]] = {}

    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for ligne in reader:
            total_csv += 1
            i_id = (ligne.get("incident_id") or "").strip()

            # 1. Doublon strict
            is_unique, motif_d = est_ligne_unique(ligne, empreintes_vues)
            if not is_unique:
                nb_doublons += 1
                journaliser(fichier, i_id, "ligne", "", motif_d, "rejet")
                continue

            if not i_id or i_id in incidents_valides:
                nb_rejets += 1
                journaliser(fichier, i_id, "incident_id", i_id, "Identifiant incident manquant ou dupliqué", "rejet")
                continue

            # 2. Statut fiabilisé (RG7)
            statut, motif_statut = fiabiliser_statut(ligne.get("statut"))
            if not statut:
                nb_rejets += 1
                journaliser(fichier, i_id, "statut", ligne.get("statut"), motif_statut, "rejet")
                continue
            if motif_statut:
                journaliser(fichier, i_id, "statut", ligne.get("statut"), motif_statut, "normalisation")

            # 3. Horodatages (signalement et résolution)
            date_sig, motif_sig = fiabiliser_horodatage(ligne.get("date_signalement"))
            if not date_sig:
                nb_rejets += 1
                journaliser(fichier, i_id, "date_signalement", ligne.get("date_signalement"), motif_sig, "rejet")
                continue
            if motif_sig:
                journaliser(fichier, i_id, "date_signalement", ligne.get("date_signalement"), motif_sig, "normalisation")

            raw_res = (ligne.get("date_resolution") or "").strip()
            date_res = None
            if raw_res:
                date_res, motif_res = fiabiliser_horodatage(raw_res)
                if not date_res:
                    nb_rejets += 1
                    journaliser(fichier, i_id, "date_resolution", raw_res, motif_res, "rejet")
                    continue
                if motif_res:
                    journaliser(fichier, i_id, "date_resolution", raw_res, motif_res, "normalisation")

            # 4. Cohérence chronologique statut / dates (RG8)
            chrono_ok, motif_chrono = valider_chronologie_incident(statut, date_sig, date_res)
            if not chrono_ok:
                nb_rejets += 1
                journaliser(fichier, i_id, "date_resolution", str(date_res), motif_chrono, "rejet")
                continue

            # 5. Cible et référence exclusive (RG6)
            cible_brute = (ligne.get("cible") or "").strip()
            velo_id = (ligne.get("velo_id") or "").strip() or None
            st_id = (ligne.get("station_id") or "").strip()
            cible, motif_cible = fiabiliser_cible_incident(cible_brute, velo_id, st_id)
            if cible is None:
                nb_rejets += 1
                journaliser(fichier, i_id, "cible", cible_brute, motif_cible, "rejet")
                continue
            if cible != cible_brute:
                journaliser(
                    fichier,
                    i_id,
                    "cible",
                    cible_brute,
                    f"Cible normalisée : '{cible_brute}' -> '{cible}'",
                    "normalisation",
                )

            # 6. Station existante si incident station
            st_valide, motif_st = valider_station_existante(st_id, stations_connues, est_facultatif=True)
            if not st_valide:
                nb_rejets += 1
                journaliser(fichier, i_id, "station_id", st_id, motif_st, "rejet")
                continue

            incidents_valides[i_id] = {
                "incident_id": i_id,
                "date_signalement": date_sig,
                "cible": cible,
                "velo_id": velo_id,
                "station_id": st_id or None,
                "type_incident": (ligne.get("type_incident") or "").strip(),
                "statut": statut,
                "date_resolution": date_res,
                "technicien": (ligne.get("technicien") or "").strip() or None,
            }

    # Insertion idempotente
    for inc in incidents_valides.values():
        stmt = text("""
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
        """)
        session.execute(stmt, inc)

    session.commit()
    nb_import = len(incidents_valides)
    print(f"[{fichier}] Total CSV: {total_csv} = Importées: {nb_import} + Rejetées: {nb_rejets} + Doublons: {nb_doublons}")
    assert total_csv == nb_import + nb_rejets + nb_doublons, f"Équation non respectée pour {fichier}"


def ecrire_rapport_audit() -> None:
    """Génère le journal d'audit CSV."""
    with open(RAPPORT_CSV, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = ["fichier_source", "identifiant", "colonne", "valeur", "motif", "decision"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(journal_audit)
    print(f"Journal d'audit généré : {RAPPORT_CSV} ({len(journal_audit)} entrées)")


def main() -> None:
    """Exécution globale de l'ingestion."""
    print("Démarrage de l'import des données réelles...")
    engine = create_engine(DATABASE_URL)

    with Session(engine) as session:
        stations_connues = importer_stations(session)
        importer_trajets(session, stations_connues)
        importer_incidents(session, stations_connues)

    ecrire_rapport_audit()
    print("Import terminé avec succès !")


if __name__ == "__main__":
    main()