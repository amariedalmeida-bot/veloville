"""Tests unitaires des règles de fiabilisation.

À compléter : un test par règle, cas nominal et cas de rejet.
"""

from api.services.fiabilisation import (
    est_ligne_unique,
    fiabiliser_horodatage,
    fiabiliser_statut,
    valider_champ_facultatif,
    valider_chronologie_incident,
    valider_duree,
    valider_station_existante,
)


# ==============================================================================
# 1. Normalisation des horodatages
# ==============================================================================

def test_fiabiliser_horodatage_nominal():
    """Cas nominal : conversion d'un horodatage valide."""
    val, err = fiabiliser_horodatage("2026-08-05 15:00")
    assert val == "2026-08-05 15:00:00"
    assert err is not None  # Signale la normalisation

    # Format déjà standard ISO
    val_iso, err_iso = fiabiliser_horodatage("2026-08-05 15:00:00")
    assert val_iso == "2026-08-05 15:00:00"
    assert err_iso is None


def test_fiabiliser_horodatage_rejet():
    """Cas de rejet : chaîne vide, None ou format non valide."""
    val_none, err_none = fiabiliser_horodatage(None)
    assert val_none is None
    assert "absent" in err_none.lower()

    val_bad, err_bad = fiabiliser_horodatage("date-invalide-99")
    assert val_bad is None
    assert "invalide" in err_bad.lower()


# ==============================================================================
# 2. Règle RG7 : Normalisation des statuts d'incident
# ==============================================================================

def test_fiabiliser_statut_nominal():
    """Cas nominal : acceptation et correction de la casse/espaces."""
    # Déjà conforme
    val, err = fiabiliser_statut("ouvert")
    assert val == "ouvert"
    assert err is None

    # Conversion de casse et espaces ('En cours' -> 'en_cours')
    val_ec, err_ec = fiabiliser_statut("En cours")
    assert val_ec == "en_cours"
    assert "corrigé" in err_ec.lower()


def test_fiabiliser_statut_rejet():
    """Cas de rejet : statut inconnu ou valeur vide."""
    val_bad, err_bad = fiabiliser_statut("en_attente_fournisseur")
    assert val_bad is None
    assert "statut inconnu" in err_bad.lower()

    val_empty, err_empty = fiabiliser_statut("")
    assert val_empty is None
    assert "vide" in err_empty.lower()


# ==============================================================================
# 3. Règle RG4 : Validation de la durée d'un trajet
# ==============================================================================

def test_valider_duree_nominal():
    """Cas nominal : durée strictement positive (> 0)."""
    ok, err = valider_duree("180")
    assert ok is True
    assert err is None

    ok_int, err_int = valider_duree(3600)
    assert ok_int is True
    assert err_int is None


def test_valider_duree_rejet():
    """Cas de rejet : durée <= 0 ou non numérique."""
    ok_zero, err_zero = valider_duree("0")
    assert ok_zero is False
    assert "RG4" in err_zero

    ok_neg, err_neg = valider_duree(-45)
    assert ok_neg is False
    assert "RG4" in err_neg

    ok_txt, err_txt = valider_duree("non_numerique")
    assert ok_txt is False
    assert "RG4" in err_txt


# ==============================================================================
# 4. Règles RG2 et RG3 : Référencement de station
# ==============================================================================

def test_valider_station_existante_nominal():
    """Cas nominal : la station est bien présente dans le référentiel."""
    stations = {"S001", "S002", "S003"}
    ok, err = valider_station_existante("S001", stations)
    assert ok is True
    assert err is None


def test_valider_station_existante_rejet():
    """Cas de rejet : station absente du référentiel ou identifiant vide."""
    stations = {"S001", "S002"}
    ok_abs, err_abs = valider_station_existante("S999", stations)
    assert ok_abs is False
    assert "RG2/RG3" in err_abs

    ok_empty, err_empty = valider_station_existante("", stations, est_facultatif=False)
    assert ok_empty is False
    assert "RG2" in err_empty


# ==============================================================================
# 5. Règle RG8 : Chronologie et cohérence des dates d'incident
# ==============================================================================

def test_valider_chronologie_incident_nominal():
    """Cas nominal : dates cohérentes selon le statut."""
    # Résolu avec date de résolution >= signalement
    ok, err = valider_chronologie_incident(
        statut="resolu",
        date_signalement_iso="2026-08-01 10:00:00",
        date_resolution_iso="2026-08-02 12:00:00",
    )
    assert ok is True
    assert err is None

    # Ouvert sans date de résolution
    ok_open, err_open = valider_chronologie_incident(
        statut="ouvert",
        date_signalement_iso="2026-08-01 10:00:00",
        date_resolution_iso=None,
    )
    assert ok_open is True
    assert err_open is None


def test_valider_chronologie_incident_rejet():
    """Cas de rejet : incohérences statut / dates."""
    # Résolu SANS date de résolution
    ok_no_res, err_no_res = valider_chronologie_incident(
        statut="resolu",
        date_signalement_iso="2026-08-01 10:00:00",
        date_resolution_iso=None,
    )
    assert ok_no_res is False
    assert "RG8" in err_no_res

    # Résolution antérieure au signalement
    ok_retro, err_retro = valider_chronologie_incident(
        statut="resolu",
        date_signalement_iso="2026-08-05 10:00:00",
        date_resolution_iso="2026-08-01 10:00:00",
    )
    assert ok_retro is False
    assert "RG8" in err_retro

    # Ouvert AVEC une date de résolution
    ok_bad_status, err_bad_status = valider_chronologie_incident(
        statut="ouvert",
        date_signalement_iso="2026-08-01 10:00:00",
        date_resolution_iso="2026-08-02 12:00:00",
    )
    assert ok_bad_status is False
    assert "RG8" in err_bad_status


# ==============================================================================
# 6. Détection des doublons stricts
# ==============================================================================

def test_est_ligne_unique():
    """Vérifie l'identification des lignes uniques et doublons."""
    vues = set()
    ligne_a = {"id": "1", "nom": "Gare"}
    ligne_doublon = {"nom": "Gare", "id": "1"}
    ligne_b = {"id": "2", "nom": "Mairie"}

    # Premier passage : unique
    ok_1, _ = est_ligne_unique(ligne_a, vues)
    assert ok_1 is True

    # Deuxième passage identique : doublon rejeté
    ok_2, err_2 = est_ligne_unique(ligne_doublon, vues)
    assert ok_2 is False
    assert "doublon" in err_2.lower()

    # Autre ligne : acceptée
    ok_3, _ = est_ligne_unique(ligne_b, vues)
    assert ok_3 is True


# ==============================================================================
# 7. Données facultatives
# ==============================================================================

def test_valider_champ_facultatif():
    """Vérifie qu'un champ vide/None passe sans erreur s'il est facultatif."""
    valeur_vide = None
    ok, val, err = valider_champ_facultatif(valeur_vide, valider_duree)
    assert ok is True
    assert val is None
    assert err is None
