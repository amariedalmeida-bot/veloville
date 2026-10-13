"""Calcul des trois indicateurs (module métier testé).

À compléter : activite_par_jour(session, date_debut, date_fin),
stations_actives(session, limite) et incidents_par_statut(session).
Les routeurs ne font qu'appeler ces fonctions.
"""
from datetime import date
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.models import Incident, Station, Trajet


def activite_par_jour(
    session: Session,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """F7 : Nombre de trajets par jour sur une période."""
    jour_col = func.date(Trajet.depart_horodatage).label("jour")
    stmt = select(jour_col, func.count(Trajet.trajet_id).label("total_trajets"))

    if date_debut:
        stmt = stmt.where(func.date(Trajet.depart_horodatage) >= date_debut)
    if date_fin:
        stmt = stmt.where(func.date(Trajet.depart_horodatage) <= date_fin)

    stmt = stmt.group_by(jour_col).order_by(jour_col.asc())
    resultats = session.execute(stmt).all()

    return [{"jour": str(r.jour), "total_trajets": r.total_trajets} for r in resultats]


def stations_actives(session: Session, limite: int = 10) -> List[Dict[str, Any]]:
    """F8 : Stations ayant le plus de mouvements (départs et arrivées)."""
    departs = (
        select(Trajet.station_depart.label("sid"), func.count(Trajet.trajet_id).label("nb_dep"))
        .group_by(Trajet.station_depart)
        .subquery()
    )
    arrivees = (
        select(Trajet.station_arrivee.label("sid"), func.count(Trajet.trajet_id).label("nb_arr"))
        .where(Trajet.station_arrivee.is_not(None))
        .group_by(Trajet.station_arrivee)
        .subquery()
    )

    nb_dep = func.coalesce(departs.c.nb_dep, 0)
    nb_arr = func.coalesce(arrivees.c.nb_arr, 0)
    total_mouv = (nb_dep + nb_arr).label("total_mouvements")

    stmt = (
        select(
            Station.station_id,
            Station.nom,
            Station.commune,
            nb_dep.label("total_departs"),
            nb_arr.label("total_arrivees"),
            total_mouv,
        )
        .outerjoin(departs, Station.station_id == departs.c.sid)
        .outerjoin(arrivees, Station.station_id == arrivees.c.sid)
        .order_by(total_mouv.desc(), Station.station_id.asc())
        .limit(limite)
    )

    resultats = session.execute(stmt).all()
    return [
        {
            "station_id": r.station_id,
            "nom": r.nom,
            "commune": r.commune,
            "total_departs": int(r.total_departs),
            "total_arrivees": int(r.total_arrivees),
            "total_mouvements": int(r.total_mouvements),
        }
        for r in resultats
    ]


def incidents_par_statut(session: Session) -> Dict[str, Any]:
    """F9 : Répartition des incidents par statut et délai moyen de résolution en heures."""
    stmt_statut = select(Incident.statut, func.count(Incident.incident_id)).group_by(Incident.statut)
    lignes_statut = session.execute(stmt_statut).all()
    repartition = {statut: compte for statut, compte in lignes_statut}

    stmt_resolus = select(Incident.date_signalement, Incident.date_resolution).where(
        Incident.statut == "resolu",
        Incident.date_resolution.is_not(None),
    )
    resolus = session.execute(stmt_resolus).all()

    if resolus:
        delais = [
            (r.date_resolution - r.date_signalement).total_seconds() / 3600.0
            for r in resolus
            if r.date_resolution >= r.date_signalement
        ]
        delai_moyen = round(sum(delais) / len(delais), 2) if delais else None
    else:
        delai_moyen = None

    return {
        "repartition": repartition,
        "delai_moyen_resolution_heures": delai_moyen,
    }