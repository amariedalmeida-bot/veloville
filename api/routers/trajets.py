"""Routeur trajets.

À compléter : GET /trajets (filtres date_debut, date_fin, station ; pagination).
"""
"""Routeur trajets.

Consultation paginée et filtrée des trajets (F4, RGPD).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Trajet
from api.securite import utilisateur_courant

router = APIRouter(prefix="/trajets", tags=["Trajets"])


class TrajetResponse(BaseModel):
    trajet_id: str
    velo_id: str
    depart_horodatage: datetime
    station_depart: str
    station_arrivee: Optional[str] = None
    duree_secondes: int
    type_usager: str
    usager_ref: Optional[str] = None

    class Config:
        from_attributes = True


class PageTrajetsResponse(BaseModel):
    total: int
    page: int
    taille_page: int
    trajets: List[TrajetResponse]


@router.get("", response_model=PageTrajetsResponse)
def lister_trajets(
    station_id: Optional[str] = Query(None, description="Filtrer par station (départ ou arrivée)"),
    date_debut: Optional[datetime] = Query(None, description="Date/heure de début (ISO)"),
    date_fin: Optional[datetime] = Query(None, description="Date/heure de fin (ISO)"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    taille_page: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(utilisateur_courant),
):
    """Consulter les trajets avec filtres et pagination (F4)."""
    requete = select(Trajet)
    requete_count = select(func.count(Trajet.trajet_id))

    if station_id:
        filtre_station = or_(
            Trajet.station_depart == station_id,
            Trajet.station_arrivee == station_id,
        )
        requete = requete.where(filtre_station)
        requete_count = requete_count.where(filtre_station)

    if date_debut:
        requete = requete.where(Trajet.depart_horodatage >= date_debut)
        requete_count = requete_count.where(Trajet.depart_horodatage >= date_debut)

    if date_fin:
        requete = requete.where(Trajet.depart_horodatage <= date_fin)
        requete_count = requete_count.where(Trajet.depart_horodatage <= date_fin)

    total = db.scalar(requete_count) or 0
    offset = (page - 1) * taille_page
    lignes = db.scalars(
        requete.order_by(Trajet.depart_horodatage.desc()).offset(offset).limit(taille_page)
    ).all()

    # RGPD 7.3 : usager_ref masqué pour la direction
    est_direction = user.get("role") == "direction"
    resultats = []
    for t in lignes:
        d = TrajetResponse.model_validate(t)
        if est_direction:
            d.usager_ref = None
        resultats.append(d)

    return PageTrajetsResponse(
        total=total,
        page=page,
        taille_page=taille_page,
        trajets=resultats,
    )