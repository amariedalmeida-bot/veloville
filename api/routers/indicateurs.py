# """Routeur indicateurs.

# À compléter : GET /indicateurs/activite-par-jour,
# GET /indicateurs/stations-actives et
# GET /indicateurs/incidents-par-statut.
# """
# """Routeur indicateurs.

# Indicateurs d'activité, de fréquentation et d'incidents (F7, F8, F9).
# """

# """Routeur indicateurs.

# Indicateurs d'activité, de fréquentation et d'incidents (F7, F8, F9).
# """

from datetime import date
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.securite import utilisateur_courant
from api.services.indicateurs import (
    activite_par_jour as calc_activite_par_jour,
    incidents_par_statut as calc_incidents_par_statut,
    stations_actives as calc_stations_actives,
)

router = APIRouter(prefix="/indicateurs", tags=["Indicateurs"])


@router.get("/activite-par-jour")
def activite_par_jour(
    date_debut: Optional[date] = Query(None),
    date_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    _user: Dict[str, Any] = Depends(utilisateur_courant),
) -> List[Dict[str, Any]]:
    """F7 : Nombre de trajets par jour."""
    return calc_activite_par_jour(db, date_debut=date_debut, date_fin=date_fin)


@router.get("/stations-actives")
def stations_actives(
    limite: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: Dict[str, Any] = Depends(utilisateur_courant),
) -> List[Dict[str, Any]]:
    """F8 : Stations les plus actives (départs et arrivées)."""
    return calc_stations_actives(db, limite=limite)


@router.get("/incidents-statut")
def incidents_statut(
    db: Session = Depends(get_db),
    _user: Dict[str, Any] = Depends(utilisateur_courant),
) -> Dict[str, Any]:
    """F9 : Répartition des incidents et délai moyen de résolution."""
    return calc_incidents_par_statut(db)