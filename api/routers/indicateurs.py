"""Routeur indicateurs.

À compléter : GET /indicateurs/activite-par-jour,
GET /indicateurs/stations-actives et
GET /indicateurs/incidents-par-statut.
"""
"""Routeur FastAPI pour les indicateurs metiers."""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Utilisateur
from api.schemas import ActiviteJour, IncidentStatut, StationActive
from api.securite import utilisateur_courant
from api.services.indicateurs import (
    activite_par_jour,
    incidents_par_statut,
    stations_actives,
)

router = APIRouter(prefix="/indicateurs", tags=["Indicateurs"])


@router.get("/activite-par-jour", response_model=List[ActiviteJour])
def obtenir_activite_par_jour(
    date_debut: Optional[date] = Query(None, description="Date de debut (YYYY-MM-DD)"),
    date_fin: Optional[date] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    _user: Utilisateur = Depends(utilisateur_courant),
):
    """Calcule le nombre de trajets par jour sur une periode donnee."""
    return activite_par_jour(session=db, date_debut=date_debut, date_fin=date_fin)


@router.get("/stations-actives", response_model=List[StationActive])
def obtenir_stations_actives(
    limite: int = Query(10, ge=1, le=100, description="Nombre maximal de stations retournees"),
    db: Session = Depends(get_db),
    _user: Utilisateur = Depends(utilisateur_courant),
):
    """Identifie les stations les plus actives (departs et arrivees)."""
    return stations_actives(session=db, limite=limite)


@router.get("/incidents-par-statut", response_model=List[IncidentStatut])
def obtenir_incidents_par_statut(
    db: Session = Depends(get_db),
    _user: Utilisateur = Depends(utilisateur_courant),
):
    """Repartition des incidents par statut et delai moyen de resolution."""
    return incidents_par_statut(session=db)