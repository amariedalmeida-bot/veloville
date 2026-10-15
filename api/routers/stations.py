"""Routeur stations.

À compléter : GET /stations (filtre commune, pagination) et GET /stations/{station_id}.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Utilisateur
from api.schemas import PageReponse, StationRead
from api.securite import utilisateur_courant
from api.services.stations import (
    recuperer_communes,
    recuperer_station_par_id,
    recuperer_stations_paginees,
)

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("/communes", response_model=list[str])
def lister_communes(
    db: Session = Depends(get_db),
    _user: Utilisateur = Depends(utilisateur_courant),
) -> list[str]:
    """Retourne les communes disponibles pour filtrer les stations."""
    return recuperer_communes(db)


@router.get("", response_model=PageReponse[StationRead])
def lister_stations(
    commune: Optional[str] = Query(None, description="Filtrer par commune"),
    page: int = Query(1, ge=1, description="Numero de la page (>= 1)"),
    taille_page: int = Query(20, ge=1, le=100, description="Nombre d'elements par page (1 a 100)"),
    db: Session = Depends(get_db),
    _user: Utilisateur = Depends(utilisateur_courant),
):
    """Liste les stations avec pagination et filtre optionnel par commune."""
    return recuperer_stations_paginees(
        db=db,
        commune=commune,
        page=page,
        taille_page=taille_page,
    )


@router.get("/{station_id}", response_model=StationRead)
def obtenir_station(
    station_id: str,
    db: Session = Depends(get_db),
    _user: Utilisateur = Depends(utilisateur_courant),
):
    """Retourne les details d'une station specifique par son identifiant."""
    station = recuperer_station_par_id(db, station_id)
    if station is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station '{station_id}' introuvable",
        )
    return station