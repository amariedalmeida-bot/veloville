"""Service métier pour la gestion des incidents."""

from math import ceil
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from api.models import Incident


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
    total_pages = ceil(total / taille_page) if total > 0 else 1
    offset = (page - 1) * taille_page
    items = requete.order_by(Incident.date_signalement.desc()).offset(offset).limit(taille_page).all()

    return {
        "total": total,
        "page": page,
        "taille_page": taille_page,
        "pages": total_pages,
        "items": items,
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

    incident.statut = nouveau_statut
    db.commit()
    db.refresh(incident)
    return incident