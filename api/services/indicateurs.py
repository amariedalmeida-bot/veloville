"""Calcul des trois indicateurs métiers (exécutés en base PostgreSQL).

Conformément à l'exigence de performance 7.1 :
Les indicateurs sont calculés par agrégation directe en base de données,
jamais en mémoire applicative.
"""

from datetime import date
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select, table, column, text
from sqlalchemy.orm import Session


def activite_par_jour(
    session: Session,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Calcule le nombre de trajets par jour sur une période donnée (F7 / REC-09)."""
    trajet = table(
        "trajet",
        column("trajet_id"),
        column("depart_horodatage"),
    )

    col_jour = func.substr(trajet.c.depart_horodatage, 1, 10).label("jour")
    stmt = select(col_jour, func.count().label("nb_trajets")).select_from(trajet)

    if date_debut:
        stmt = stmt.where(func.substr(trajet.c.depart_horodatage, 1, 10) >= str(date_debut))
    if date_fin:
        stmt = stmt.where(func.substr(trajet.c.depart_horodatage, 1, 10) <= str(date_fin))

    stmt = stmt.group_by(col_jour).order_by(col_jour.asc())

    resultats = session.execute(stmt).all()

    return [
        {
            "jour": str(ligne[0]),
            "nb_trajets": int(ligne[1]),
        }
        for ligne in resultats
    ]


def stations_actives(
    session: Session,
    limite: int = 10,
) -> List[Dict[str, Any]]:
    """Identifie les stations les plus actives (départs et arrivées) (F8)."""
    station = table("station", column("station_id"), column("nom"), column("commune"))
    trajet = table(
        "trajet",
        column("station_depart"),
        column("station_arrivee"),
    )

    departs = (
        select(trajet.c.station_depart.label("s_id"), func.count().label("nb"))
        .group_by(trajet.c.station_depart)
        .subquery()
    )

    arrivees = (
        select(trajet.c.station_arrivee.label("s_id"), func.count().label("nb"))
        .where(trajet.c.station_arrivee.isnot(None))
        .group_by(trajet.c.station_arrivee)
        .subquery()
    )

    nb_dep = func.coalesce(departs.c.nb, 0)
    nb_arr = func.coalesce(arrivees.c.nb, 0)
    total = (nb_dep + nb_arr).label("total_trajets")

    stmt = (
        select(
            station.c.station_id,
            station.c.nom,
            station.c.commune,
            nb_dep.label("nb_departs"),
            nb_arr.label("nb_arrivees"),
            total,
        )
        .outerjoin(departs, station.c.station_id == departs.c.s_id)
        .outerjoin(arrivees, station.c.station_id == arrivees.c.s_id)
        .order_by(total.desc(), station.c.nom.asc())
        .limit(limite)
    )

    resultats = session.execute(stmt).all()

    return [
        {
            "station_id": str(ligne[0]),
            "nom": str(ligne[1]),
            "commune": str(ligne[2]),
            "nb_departs": int(ligne[3]),
            "nb_arrivees": int(ligne[4]),
            "total_trajets": int(ligne[5]),
        }
        for ligne in resultats
    ]


def incidents_par_statut(
    session: Session,
) -> List[Dict[str, Any]]:
    """Répartition des incidents par statut et calcul du délai moyen de résolution (F9)."""
    incident = table(
        "incident",
        column("statut"),
        column("date_signalement"),
        column("date_resolution"),
    )

    dialect_name = session.bind.dialect.name if session.bind else "postgresql"

    if dialect_name == "sqlite":
        delai_expr = func.avg(
            (func.julianday(incident.c.date_resolution) - func.julianday(incident.c.date_signalement)) * 24.0
        )
    else:
        delai_expr = func.round(
            func.avg(
                func.extract("epoch", text("date_resolution - date_signalement")) / 3600
            ),
            1,
        )

    stmt = (
        select(
            incident.c.statut,
            func.count().label("nb_incidents"),
            delai_expr.label("delai_moyen_heures"),
        )
        .group_by(incident.c.statut)
        .order_by(incident.c.statut.asc())
    )

    resultats = session.execute(stmt).all()

    return [
        {
            "statut": str(ligne[0]),
            "nb_incidents": int(ligne[1]),
            "delai_moyen_heures": (
                round(float(ligne[2]), 1) if ligne[2] is not None else None
            ),
        }
        for ligne in resultats
    ]