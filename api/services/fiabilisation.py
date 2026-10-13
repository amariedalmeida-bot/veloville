"""Règles de fiabilisation des données (module métier testé).

À compléter : fonctions pures, sans accès à la base, qui normalisent ou rejettent
une valeur ou une ligne : horodatages, identifiants de vélo, statuts
d'incident, durées, références de station, cohérence des dates,
doublons. Chaque fonction retourne la valeur normalisée ou signale le
motif de rejet. Ces fonctions sont appelées par scripts/importer.py et
couvertes par tests/unit/.
"""
from datetime import datetime
from typing import Any, Dict, Optional, Set, Tuple


def normaliser_chaine(valeur: Any) -> Optional[str]:
    """Nettoie les chaînes de caractères (espaces superflus, vides -> None)."""
    if valeur is None:
        return None
    val_str = str(valeur).strip()
    return val_str if val_str else None


def valider_station(ligne: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Valide et normalise une station selon RG1."""
    station_id = normaliser_chaine(ligne.get("station_id"))
    nom = normaliser_chaine(ligne.get("nom"))
    commune = normaliser_chaine(ligne.get("commune"))

    if not station_id or not nom or not commune:
        return None, "Champs obligatoires manquants (station_id, nom, commune)"

    try:
        capacite = int(ligne["capacite"])
        if capacite <= 0:
            return None, "Capacité négative ou nulle (RG1)"
    except (ValueError, TypeError, KeyError):
        return None, "Format de capacité invalide"

    try:
        latitude = float(ligne["latitude"])
        longitude = float(ligne["longitude"])
    except (ValueError, TypeError, KeyError):
        return None, "Coordonnées géographiques invalides"

    try:
        date_str = normaliser_chaine(ligne.get("date_mise_en_service"))
        date_service = datetime.fromisoformat(date_str).date()
    except (ValueError, TypeError):
        return None, "Format de date de mise en service invalide"

    return {
        "station_id": station_id,
        "nom": nom,
        "commune": commune,
        "capacite": capacite,
        "latitude": latitude,
        "longitude": longitude,
        "date_mise_en_service": date_service,
    }, None


def valider_trajet(
    ligne: Dict[str, Any], stations_connues: Set[str]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Valide et normalise un trajet selon RG2, RG3, RG4, RG5."""
    trajet_id = normaliser_chaine(ligne.get("trajet_id"))
    velo_id = normaliser_chaine(ligne.get("velo_id"))
    st_depart = normaliser_chaine(ligne.get("station_depart"))
    st_arrivee = normaliser_chaine(ligne.get("station_arrivee"))
    type_usager = normaliser_chaine(ligne.get("type_usager"))
    usager_ref = normaliser_chaine(ligne.get("usager_ref"))

    if not trajet_id or not velo_id or not st_depart or not type_usager:
        return None, "Champs obligatoires manquants pour le trajet"

    # RG2 : station_depart obligatoire et présente dans le référentiel
    if st_depart not in stations_connues:
        return None, f"Station de départ inconnue dans le référentiel: {st_depart} (RG2)"

    # RG2 et RG3 : station_arrivee optionnelle, mais doit exister si présente
    if st_arrivee and st_arrivee not in stations_connues:
        return None, f"Station d'arrivée inconnue dans le référentiel: {st_arrivee} (RG2)"

    # RG4 : durée strictement positive
    try:
        duree = int(ligne["duree_secondes"])
        if duree <= 0:
            return None, "Durée de trajet négative ou nulle (RG4)"
    except (ValueError, TypeError, KeyError):
        return None, "Format de durée invalide"

    # Horodatage
    try:
        dep_str = normaliser_chaine(ligne.get("depart_horodatage"))
        dep_dt = datetime.fromisoformat(dep_str)
    except (ValueError, TypeError):
        return None, "Horodatage de départ invalide"

    # RG5 : usager occasionnel -> pas de pseudonyme conservé
    if type_usager.lower() in ("occasionnel", "visiteur"):
        usager_ref = None

    return {
        "trajet_id": trajet_id,
        "velo_id": velo_id,
        "depart_horodatage": dep_dt,
        "station_depart": st_depart,
        "station_arrivee": st_arrivee,
        "duree_secondes": duree,
        "type_usager": type_usager,
        "usager_ref": usager_ref,
    }, None


def valider_incident(
    ligne: Dict[str, Any], stations_connues: Set[str]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Valide et normalise un incident selon RG6, RG7, RG8."""
    inc_id = normaliser_chaine(ligne.get("incident_id"))
    cible = normaliser_chaine(ligne.get("cible"))
    velo_id = normaliser_chaine(ligne.get("velo_id"))
    st_id = normaliser_chaine(ligne.get("station_id"))
    type_inc = normaliser_chaine(ligne.get("type_incident"))
    statut_raw = normaliser_chaine(ligne.get("statut"))
    technicien = normaliser_chaine(ligne.get("technicien"))

    if not inc_id or not cible or not type_inc or not statut_raw:
        return None, "Champs obligatoires manquants pour l'incident"

    cible = cible.lower()
    statut = statut_raw.lower()

    # RG7 : statuts autorisés
    if statut not in ("ouvert", "en_cours", "resolu"):
        return None, f"Statut non autorisé: {statut} (RG7)"

    # RG6 : incident vise vélo OU station, jamais les deux ni aucun
    if cible == "velo":
        if not velo_id or st_id:
            return None, "Cible vélo : velo_id requis et station_id doit être vide (RG6)"
    elif cible == "station":
        if not st_id or velo_id:
            return None, "Cible station : station_id requis et velo_id doit être vide (RG6)"
        if st_id not in stations_connues:
            return None, f"Station visée inconnue dans le référentiel: {st_id} (RG6)"
    else:
        return None, f"Valeur de cible invalide: {cible} (RG6)"

    # Dates
    try:
        date_sig_str = normaliser_chaine(ligne.get("date_signalement"))
        date_sig = datetime.fromisoformat(date_sig_str)
    except (ValueError, TypeError):
        return None, "Date de signalement invalide"

    date_res = None
    date_res_str = normaliser_chaine(ligne.get("date_resolution"))
    if date_res_str:
        try:
            date_res = datetime.fromisoformat(date_res_str)
        except (ValueError, TypeError):
            return None, "Format de date de résolution invalide"

    # RG8 : date de résolution si et seulement si résolu, et >= signalement
    if statut == "resolu":
        if not date_res:
            return None, "Incident résolu sans date de résolution (RG8)"
        if date_res < date_sig:
            return None, "Date de résolution antérieure à la date de signalement (RG8)"
    else:
        if date_res is not None:
            return None, "Date de résolution renseignée sur un incident non résolu (RG8)"

    return {
        "incident_id": inc_id,
        "date_signalement": date_sig,
        "cible": cible,
        "velo_id": velo_id,
        "station_id": st_id,
        "type_incident": type_inc,
        "statut": statut,
        "date_resolution": date_res,
        "technicien": technicien,
    }, None