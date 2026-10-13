"""Modèles ORM SQLAlchemy : Station, Trajet, Incident, Utilisateur.

À compléter : déclarer les quatre tables conformément à sql/schema.sql.
"""
"""Modèles ORM SQLAlchemy : Station, Trajet, Incident, Utilisateur.

Déclaration des quatre tables conformément à sql/schema.sql.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from api.database import Base


class Station(Base):
    __tablename__ = "station"

    station_id = Column(String(32), primary_key=True)
    nom = Column(String(128), nullable=False)
    commune = Column(String(128), nullable=False)
    capacite = Column(Integer, nullable=False)
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    date_mise_en_service = Column(Date, nullable=False)

    __table_args__ = (
        CheckConstraint("capacite > 0", name="chk_station_capacite_positive"),
    )


class Trajet(Base):
    __tablename__ = "trajet"

    trajet_id = Column(String(32), primary_key=True)
    velo_id = Column(String(32), nullable=False)
    depart_horodatage = Column(DateTime, nullable=False)
    station_depart = Column(String(32), ForeignKey("station.station_id"), nullable=False)
    station_arrivee = Column(String(32), ForeignKey("station.station_id"), nullable=True)
    duree_secondes = Column(Integer, nullable=False)
    type_usager = Column(String(32), nullable=False)
    usager_ref = Column(String(64), nullable=True)

    station_depart_rel = relationship("Station", foreign_keys=[station_depart])
    station_arrivee_rel = relationship("Station", foreign_keys=[station_arrivee])

    __table_args__ = (
        CheckConstraint("duree_secondes > 0", name="chk_trajet_duree_positive"),
    )


class Incident(Base):
    __tablename__ = "incident"

    incident_id = Column(String(32), primary_key=True)
    date_signalement = Column(DateTime, nullable=False)
    cible = Column(String(16), nullable=False)
    velo_id = Column(String(32), nullable=True)
    station_id = Column(String(32), ForeignKey("station.station_id"), nullable=True)
    type_incident = Column(String(64), nullable=False)
    statut = Column(String(16), nullable=False)
    date_resolution = Column(DateTime, nullable=True)
    technicien = Column(String(64), nullable=True)

    station_rel = relationship("Station", foreign_keys=[station_id])

    __table_args__ = (
        CheckConstraint("cible IN ('velo', 'station')", name="chk_incident_cible"),
        CheckConstraint("statut IN ('ouvert', 'en_cours', 'resolu')", name="chk_incident_statut"),
    )


class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id_utilisateur = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    mot_de_passe_hash = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('exploitant', 'direction')", name="chk_utilisateur_role"),
    )