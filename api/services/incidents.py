"""Service métier pour la gestion des incidents."""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from api.models import Incident


class TransitionStatutInvalide(ValueError):
    """Indique qu'une transition de statut ne respecte pas la règle RG7."""


_TRANSITIONS_AUTORISEES = {
    "ouvert": {"en_cours", "resolu"},
    "en_cours": {"resolu"},
    "resolu": set(),
}


def recuperer_incidents_pagines(
    db: Session,
    statut: Optional[str] = None,
    page: int = 1,
    taille_page: int = 20,
) -> Dict[str, Any]:
    """Récupère la liste paginée des incidents avec filtre optionnel sur le statut."""
    requete = db.query(Incident)

    if statut:
        requete = requete.filter(Incident.statut == statut.strip())

    total = requete.count()
    offset = (page - 1) * taille_page
    resultats = requete.order_by(Incident.date_signalement.desc()).offset(offset).limit(taille_page).all()

    return {
        "total": total,
        "page": page,
        "taille_page": taille_page,
        "resultats": resultats,
    }


def mettre_a_jour_statut_incident(
    db: Session,
    incident_id: str,
    nouveau_statut: str,
) -> Optional[Incident]:
    """Modifie le statut d'un incident en base de données."""
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if incident is None:
        return None

    if nouveau_statut not in _TRANSITIONS_AUTORISEES.get(incident.statut, set()):
        raise TransitionStatutInvalide

    if nouveau_statut == "resolu":
        date_resolution = datetime.now()
        if date_resolution < incident.date_signalement:
            raise TransitionStatutInvalide
    else:
        date_resolution = None

    incident.statut = nouveau_statut
    incident.date_resolution = date_resolution
    db.commit()
    db.refresh(incident)
    return incident