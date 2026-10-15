"""Service métier pour la consultation des trajets."""

from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.models import Trajet


def recuperer_trajets_pagines(
    db: Session,
    station: Optional[str] = None,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    page: int = 1,
    taille_page: int = 20,
) -> Dict[str, Any]:
    """Récupère la liste paginée des trajets avec filtres optionnels."""
    requete = db.query(Trajet)

    if station:
        station_id = station.strip()
        requete = requete.filter(
            or_(
                Trajet.station_depart == station_id,
                Trajet.station_arrivee == station_id,
            )
        )
    if date_debut:
        debut = datetime.combine(date_debut, time.min)
        requete = requete.filter(Trajet.depart_horodatage >= debut)
    if date_fin:
        fin_exclusive = datetime.combine(date_fin + timedelta(days=1), time.min)
        requete = requete.filter(Trajet.depart_horodatage < fin_exclusive)

    total = requete.count()
    offset = (page - 1) * taille_page
    resultats = requete.order_by(Trajet.depart_horodatage.asc()).offset(offset).limit(taille_page).all()

    return {
        "total": total,
        "page": page,
        "taille_page": taille_page,
        "resultats": resultats,
    }