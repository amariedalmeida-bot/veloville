"""Routeur incidents.

À compléter : GET /incidents (filtre statut, pagination) et
PUT /incidents/{incident_id}/statut (rôle exploitant).
"""


from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Utilisateur
from api.schemas import IncidentRead, IncidentStatutUpdate, PageReponse
from api.securite import exiger_role, utilisateur_courant
from api.services.incidents import (
    TransitionStatutInvalide,
    mettre_a_jour_statut_incident,
    recuperer_incidents_pagines,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=PageReponse[IncidentRead])
def lister_incidents(
    statut: Optional[str] = Query(None, description="Filtrer par statut ('ouvert', 'en_cours', 'resolu')"),
    page: int = Query(1, ge=1, description="Numéro de la page (>= 1)"),
    taille_page: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page (1 à 100)"),
    db: Session = Depends(get_db),
    _user: Utilisateur = Depends(utilisateur_courant),
):
    """Liste les incidents avec pagination et filtre optionnel par statut."""
    return recuperer_incidents_pagines(
        db=db,
        statut=statut,
        page=page,
        taille_page=taille_page,
    )


@router.put("/{incident_id}/statut", response_model=IncidentRead)
def modifier_statut(
    incident_id: str,
    payload: IncidentStatutUpdate,
    db: Session = Depends(get_db),
    _user: Utilisateur = Depends(exiger_role("exploitant")),
):
    """Modifie le statut d'un incident (réservé au rôle exploitant)."""
    try:
        incident = mettre_a_jour_statut_incident(
            db=db,
            incident_id=incident_id,
            nouveau_statut=payload.statut,
        )
    except TransitionStatutInvalide as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transition de statut non autorisée.",
        ) from exc

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' introuvable",
        )
    return incident