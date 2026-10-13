"""Routeur incidents.

À compléter : GET /incidents (filtre statut, pagination) et
PUT /incidents/{incident_id}/statut (rôle exploitant).
"""
"""Routeur incidents.

Consultation (F5) et mise à jour de statut (F6, RG7, RG8).
"""
"""Routeur incidents.

À compléter : GET /incidents (filtre statut, pagination) et
PUT /incidents/{incident_id}/statut (rôle exploitant).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Incident
from api.securite import exiger_role, utilisateur_courant

router = APIRouter(prefix="/incidents", tags=["Incidents"])

TRANSITIONS_AUTORISEES = {
    "ouvert": {"en_cours", "resolu"},
    "en_cours": {"resolu"},
    "resolu": set(),
}


class IncidentResponse(BaseModel):
    incident_id: str
    date_signalement: datetime
    cible: str
    velo_id: Optional[str] = None
    station_id: Optional[str] = None
    type_incident: str
    statut: str
    date_resolution: Optional[datetime] = None
    technicien: Optional[str] = None

    class Config:
        from_attributes = True


class PageIncidentsResponse(BaseModel):
    total: int
    page: int
    taille_page: int
    incidents: List[IncidentResponse]


class MajStatutIncidentRequest(BaseModel):
    nouveau_statut: str
    technicien: Optional[str] = None


@router.get("", response_model=PageIncidentsResponse)
def lister_incidents(
    statut: Optional[str] = Query(None, description="Filtrer par statut: ouvert, en_cours, resolu"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    taille_page: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
    db: Session = Depends(get_db),
    _user: Dict[str, Any] = Depends(utilisateur_courant),
):
    """Consulter les incidents avec filtre par statut et pagination (F5)."""
    requete = select(Incident)
    requete_count = select(func.count(Incident.incident_id))

    if statut:
        statut_nettoye = statut.strip().lower()
        requete = requete.where(Incident.statut == statut_nettoye)
        requete_count = requete_count.where(Incident.statut == statut_nettoye)

    total = db.scalar(requete_count) or 0
    offset = (page - 1) * taille_page
    incidents = db.scalars(
        requete.order_by(Incident.date_signalement.desc()).offset(offset).limit(taille_page)
    ).all()

    return PageIncidentsResponse(
        total=total,
        page=page,
        taille_page=taille_page,
        incidents=incidents,
    )


@router.put("/{incident_id}/statut", response_model=IncidentResponse)
@router.patch("/{incident_id}/statut", response_model=IncidentResponse)
def modifier_statut_incident(
    incident_id: str,
    payload: MajStatutIncidentRequest,
    db: Session = Depends(get_db),
    _user: Dict[str, Any] = Depends(exiger_role("exploitant")),
):
    """Faire évoluer le statut d'un incident (F6, réservé exploitant)."""
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' introuvable.",
        )

    nouveau = payload.nouveau_statut.strip().lower()
    statut_actuel = incident.statut.lower()

    # RG7 : transitions autorisées
    if nouveau not in TRANSITIONS_AUTORISEES.get(statut_actuel, set()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transition interdite de '{statut_actuel}' vers '{nouveau}' (RG7).",
        )

    incident.statut = nouveau
    if payload.technicien:
        incident.technicien = payload.technicien.strip()

    # RG8 : date de résolution automatique lors du passage à résolu
    if nouveau == "resolu":
        incident.date_resolution = datetime.now(timezone.utc)

    db.commit()
    db.refresh(incident)
    return incident