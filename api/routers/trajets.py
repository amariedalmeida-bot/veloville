"""Routeur trajets.

À compléter : GET /trajets (filtres date_debut, date_fin, station ; pagination).
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Utilisateur
from api.schemas import PageReponse, TrajetRead
from api.securite import utilisateur_courant
from api.services.trajets import recuperer_trajets_pagines

router = APIRouter(prefix="/trajets", tags=["Trajets"])


@router.get("", response_model=PageReponse[TrajetRead])
def lister_trajets(
    station: Optional[str] = Query(None, description="Filtrer par station de départ ou d'arrivée"),
    date_debut: Optional[date] = Query(None, description="Date de départ minimale incluse (AAAA-MM-JJ)"),
    date_fin: Optional[date] = Query(None, description="Date de départ maximale incluse (AAAA-MM-JJ)"),
    page: int = Query(1, ge=1, description="Numéro de la page (>= 1)"),
    taille_page: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page (1 à 100)"),
    db: Session = Depends(get_db),
    _user: Utilisateur = Depends(utilisateur_courant),
):
    """Liste les trajets avec pagination et filtres optionnels."""
    return recuperer_trajets_pagines(
        db=db,
        station=station,
        date_debut=date_debut,
        date_fin=date_fin,
        page=page,
        taille_page=taille_page,
    )