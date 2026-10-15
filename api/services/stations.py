"""Service métier pour la consultation des stations."""

from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.models import Station


def recuperer_communes(db: Session) -> List[str]:
    """Retourne les communes présentes dans le référentiel des stations."""
    communes = (
        db.query(Station.commune)
        .distinct()
        .order_by(Station.commune)
        .all()
    )
    return [commune for (commune,) in communes]


def recuperer_stations_paginees(
    db: Session,
    commune: Optional[str] = None,
    page: int = 1,
    taille_page: int = 20,
) -> Dict[str, Any]:
    """Récupère la liste paginée des stations avec filtre optionnel sur la commune."""
    # 1. On initialise la requête de base sur la table Station
    requete = db.query(Station)

    # 2. Si l'utilisateur fournit une commune, on filtre sans tenir compte de la casse
    if commune:
        requete = requete.filter(func.lower(Station.commune) == commune.strip().lower())

    # 3. On compte le total avant de découper en pages
    total = requete.count()

    # 4. On applique le décalage (offset) et la limite de taille pour la page demandée
    offset = (page - 1) * taille_page
    resultats = requete.order_by(Station.station_id).offset(offset).limit(taille_page).all()

    # 5. On renvoie le dictionnaire conforme au contrat de pagination
    return {
        "total": total,
        "page": page,
        "taille_page": taille_page,
        "resultats": resultats,
    }


def recuperer_station_par_id(db: Session, station_id: str) -> Optional[Station]:
    """Récupère une station unique par son identifiant."""
    return db.query(Station).filter(Station.station_id == station_id).first()