"""Règles de fiabilisation des données (module métier testé).

À compléter : fonctions pures, sans accès à la base, qui normalisent ou rejettent
une valeur ou une ligne : horodatages, identifiants de vélo, statuts
d'incident, durées, références de station, cohérence des dates,
doublons. Chaque fonction retourne la valeur normalisée ou signale le
motif de rejet. Ces fonctions sont appelées par scripts/importer.py et
couvertes par tests/unit/.
"""
"""Module de fiabilisation et de validation des données VéloVille.

Contient les fonctions pures pour :
- La normalisation des horodatages et statuts
- La validation des règles métier (RG2, RG3, RG4, RG8)
- La détection des doublons stricts
- La gestion des champs facultatifs
"""

from datetime import datetime
from typing import Any, Optional, Set, Tuple


# ==============================================================================
# FIABILISATION
# ==============================================================================

def fiabiliser_horodatage(valeur: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Fiabilise un horodatage vers le standard ISO 'YYYY-MM-DD HH:MM:SS'."""
    if valeur is None:
        return None, "Horodatage absent"

    texte = str(valeur).strip()
    if not texte:
        return None, "Horodatage vide"

    formats_acceptes = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
    )

    for format_source in formats_acceptes:
        try:
            date_objet = datetime.strptime(texte, format_source)
            if len(texte) <= 10 and ":" not in texte:
                format_cible = date_objet.strftime("%Y-%m-%d")
            else:
                format_cible = date_objet.strftime("%Y-%m-%d %H:%M:%S")

            if texte != format_cible:
                return format_cible, f"Format converti : '{texte}' -> '{format_cible}'"

            return format_cible, None
        except ValueError:
            continue

    return None, f"Format d'horodatage non reconnu ou invalide : '{texte}'"


def fiabiliser_statut(valeur: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Fiabilise la casse et les espaces d'un statut d'incident (RG7)."""
    if valeur is None:
        return None, "Statut absent"

    texte = str(valeur).strip()
    if not texte:
        return None, "Statut vide"

    statut_nettoye = texte.lower().replace(" ", "_")
    statuts_valides = {"ouvert", "en_cours", "resolu"}

    # Variantes courantes
    mapping = {
        "en cours": "en_cours",
        "en_cours": "en_cours",
        "ouvert": "ouvert",
        "resolu": "resolu",
        "résolu": "resolu",
        "clos": "resolu",
    }
    statut_final = mapping.get(statut_nettoye, statut_nettoye)

    if statut_final in statuts_valides:
        if texte != statut_final:
            return statut_final, f"Statut corrigé : '{texte}' -> '{statut_final}'"
        return statut_final, None

    return None, f"Statut inconnu : '{texte}'"


# ==============================================================================
# VALIDATION DES RÈGLES MÉTIER
# ==============================================================================

def valider_duree(valeur: Any) -> Tuple[bool, Optional[str]]:
    """Règle RG4 : la durée d'un trajet doit être strictement positive (> 0)."""
    try:
        duree = int(valeur)
        if duree <= 0:
            return False, f"Rejet RG4 : durée invalide ({duree} s), attendu > 0"
        return True, None
    except (ValueError, TypeError):
        return False, f"Rejet RG4 : durée non numérique ({valeur})"


def valider_station_existante(
    station_id: Optional[str],
    stations_connues: Set[str],
    est_facultatif: bool = False,
) -> Tuple[bool, Optional[str]]:
    """Règles RG2 et RG3 : intégrité référentielle des stations."""
    if not station_id or not str(station_id).strip():
        if est_facultatif:
            return True, None
        return False, "Rejet RG2 : identifiant de station obligatoire manquant"

    id_propre = str(station_id).strip()
    if id_propre not in stations_connues:
        return False, f"Rejet RG2/RG3 : station inconnue ({id_propre})"

    return True, None


def valider_chronologie_incident(
    statut: str,
    date_signalement_iso: str,
    date_resolution_iso: Optional[str],
) -> Tuple[bool, Optional[str]]:
    """Règle RG8 : cohérence temporelle statut et dates de résolution."""
    if statut == "resolu":
        if not date_resolution_iso or not str(date_resolution_iso).strip():
            return False, "Rejet RG8 : incident résolu sans date de résolution renseignée"

        if date_resolution_iso < date_signalement_iso:
            return False, (
                f"Rejet RG8 : résolution ({date_resolution_iso}) "
                f"antérieure au signalement ({date_signalement_iso})"
            )
        return True, None

    if date_resolution_iso and str(date_resolution_iso).strip():
        return False, f"Rejet RG8 : un incident '{statut}' ne peut pas avoir de date de résolution"

    return True, None


# ==============================================================================
# GESTION DES DOUBLONS
# ==============================================================================

def est_ligne_unique(ligne: dict, empreintes_vues: set) -> Tuple[bool, Optional[str]]:
    """Vérifie si une ligne est strictement identique à une ligne déjà traitée."""
    empreinte = tuple(sorted((k, str(v).strip()) for k, v in ligne.items()))

    if empreinte in empreintes_vues:
        return False, "Rejet doublon : ligne strictement identique déjà traitée"

    empreintes_vues.add(empreinte)
    return True, None


# ==============================================================================
# GESTION DES DONNÉES FACULTATIVES
# ==============================================================================

def valider_champ_facultatif(
    valeur: Optional[Any],
    fonction_validation,
    **kwargs,
) -> Tuple[bool, Optional[Any], Optional[str]]:
    """Gère l'absence d'une donnée facultative sans entraîner de rejet."""
    if valeur is None or str(valeur).strip() == "":
        return True, None, None

    return fonction_validation(valeur, **kwargs)