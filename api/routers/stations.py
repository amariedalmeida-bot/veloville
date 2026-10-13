"""Routeur stations.

À compléter : GET /stations (filtre commune, pagination) et GET /stations/{station_id}.
"""
"""Routeur stations.

Consultation des stations du réseau VéloVille (F2, F3).
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Station
from api.securite import utilisateur_courant

router = APIRouter(prefix="/stations", tags=["Stations"])


class StationResponse(BaseModel):
    station_id: str
    nom: str
    commune: str
    capacite: int
    latitude: float
    longitude: float
    date_mise_en_service: Any

    class Config:
        from_attributes = True


class PageStationsResponse(BaseModel):
    total: int
    page: int
    taille_page: int
    stations: List[StationResponse]


@router.get("", response_model=PageStationsResponse)
def lister_stations(
    commune: Optional[str] = Query(None, description="Filtrer par nom de commune"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    taille_page: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
    db: Session = Depends(get_db),
    _user: Dict[str, Any] = Depends(utilisateur_courant),
):
    """Lister les stations avec pagination et filtre par commune (F2)."""
    requete = select(Station)
    requete_total = select(func.count(Station.station_id))

    if commune:
        requete = requete.where(Station.commune.ilike(f"%{commune}%"))
        requete_total = requete_total.where(Station.commune.ilike(f"%{commune}%"))

    total = db.scalar(requete_total) or 0
    offset = (page - 1) * taille_page
    stations = db.scalars(requete.order_by(Station.station_id).offset(offset).limit(taille_page)).all()

    return PageStationsResponse(
        total=total,
        page=page,
        taille_page=taille_page,
        stations=stations,
    )


@router.get("/{station_id}", response_model=StationResponse)
def obtenir_station(
    station_id: str,
    db: Session = Depends(get_db),
    _user: Dict[str, Any] = Depends(utilisateur_courant),
):
    """Consulter une station par son identifiant unique (F3)."""
    station = db.get(Station, station_id)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station '{station_id}' introuvable.",
        )
    return station