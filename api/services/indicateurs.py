"""Calcul des trois indicateurs metiers (executes en base PostgreSQL et SQLite pour les tests).

Conformement a l exigence de performance 7.1 :
Les indicateurs sont calcules par aggregation directe en base de donnees,
jamais en memoire applicative.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Date, String, cast, column, func, select, table, text
from sqlalchemy.orm import Session


def activite_par_jour(
    session: Session,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Calcule le nombre de trajets par jour et la duree moyenne sur une periode donnee (F7 / REC-09)."""
    trajet = table(
        "trajet",
        column("trajet_id"),
        column("depart_horodatage"),
        column("duree_secondes"),
    )

    dialect_name = session.bind.dialect.name if session.bind else "postgresql"

    # SQLite (tests unitaires) stocke du texte ISO, PostgreSQL stocke du TIMESTAMP
    if dialect_name == "sqlite":
        col_jour = func.substr(cast(trajet.c.depart_horodatage, String), 1, 10).label("jour")
        filtre_debut = func.substr(cast(trajet.c.depart_horodatage, String), 1, 10) >= str(date_debut) if date_debut else None
        filtre_fin = func.substr(cast(trajet.c.depart_horodatage, String), 1, 10) <= str(date_fin) if date_fin else None
    else:
        col_jour = cast(trajet.c.depart_horodatage, Date).label("jour")
        filtre_debut = cast(trajet.c.depart_horodatage, Date) >= date_debut if date_debut else None
        filtre_fin = cast(trajet.c.depart_horodatage, Date) <= date_fin if date_fin else None

    duree_expr = func.round(func.avg(trajet.c.duree_secondes), 1)

    stmt = select(
        col_jour,
        func.count().label("nombre_trajets"),
        duree_expr.label("duree_moyenne_secondes"),
    ).select_from(trajet)

    if filtre_debut is not None:
        stmt = stmt.where(filtre_debut)
    if filtre_fin is not None:
        stmt = stmt.where(filtre_fin)

    stmt = stmt.group_by(col_jour).order_by(col_jour.asc())

    resultats = session.execute(stmt).all()

    sorties = []
    for ligne in resultats:
        val_date = ligne[0]
        if isinstance(val_date, str):
            val_date_str = val_date[:10]
            val_date_obj = datetime.strptime(val_date_str, "%Y-%m-%d").date()
        elif isinstance(val_date, (date, datetime)):
            val_date_obj = val_date if isinstance(val_date, date) else val_date.date()
            val_date_str = val_date_obj.isoformat()
        else:
            val_date_str = str(val_date)
            val_date_obj = date.fromisoformat(val_date_str)

        nb = int(ligne[1])
        duree = round(float(ligne[2]), 1) if ligne[2] is not None else 0.0

        sorties.append(
            {
                "jour": val_date_str,
                "date": val_date_obj,
                "nb_trajets": nb,
                "nombre_trajets": nb,
                "total_trajets": nb,
                "duree_moyenne_secondes": duree,
            }
        )

    return sorties


def stations_actives(
    session: Session,
    limite: int = 10,
) -> List[Dict[str, Any]]:
    """Identifie les stations les plus actives (departs et arrivees) (F8)."""
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
    """Repartition des incidents par statut et calcul du delai moyen de resolution (F9)."""
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
