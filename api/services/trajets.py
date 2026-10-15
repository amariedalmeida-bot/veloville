"""Service métier pour la consultation des trajets."""

from math import ceil
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from api.models import Trajet


def recuperer_trajets_pagines(
    db: Session,
    station_depart: Optional[str] = None,
    date_debut: Optional[str] = None,
    page: int = 1,
    taille_page: int = 20,
) -> Dict[str, Any]:
    """Récupère la liste paginée des trajets avec filtres optionnels."""
    requete = db.query(Trajet)

    if station_depart:
        requete = requete.filter(Trajet.station_depart == station_depart.strip())
    if date_debut:
        requete = requete.filter(Trajet.depart_horodatage >= date_debut.strip())

    total = requete.count()
    total_pages = ceil(total / taille_page) if total > 0 else 1
    offset = (page - 1) * taille_page
    items = requete.order_by(Trajet.depart_horodatage.desc()).offset(offset).limit(taille_page).all()

    return {
        "total": total,
        "page": page,
        "taille_page": taille_page,
        "pages": total_pages,
        "items": items,
    }