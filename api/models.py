"""Modèles ORM SQLAlchemy : Station, Trajet, Incident, Utilisateur.

À compléter : déclarer les quatre tables conformément à sql/schema.sql.
"""
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from api.database import Base


class Station(Base):
    __tablename__ = "station"

    station_id = Column(String(50), primary_key=True)
    nom = Column(String(255), nullable=False)
    commune = Column(String(100), nullable=False)
    capacite = Column(Integer, nullable=False, default=0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    date_mise_en_service = Column(Date, nullable=True)

    # Relations
    trajets_depart = relationship("Trajet", back_populates="station_dep", foreign_keys="Trajet.station_depart")
    trajets_arrivee = relationship("Trajet", back_populates="station_arr", foreign_keys="Trajet.station_arrivee")
    incidents = relationship("Incident", back_populates="station")


class Trajet(Base):
    __tablename__ = "trajet"

    trajet_id = Column(String(50), primary_key=True)
    velo_id = Column(String(50), nullable=True)
    depart_horodatage = Column(DateTime, nullable=False)
    station_depart = Column(String(50), ForeignKey("station.station_id"), nullable=False)
    station_arrivee = Column(String(50), ForeignKey("station.station_id"), nullable=True)
    duree_secondes = Column(Integer, nullable=False, default=0)
    type_usager = Column(String(50), nullable=True)
    usager_ref = Column(String(100), nullable=True)

    station_dep = relationship("Station", foreign_keys=[station_depart], back_populates="trajets_depart")
    station_arr = relationship("Station", foreign_keys=[station_arrivee], back_populates="trajets_arrivee")


class Incident(Base):
    __tablename__ = "incident"

    incident_id = Column(String(50), primary_key=True)
    date_signalement = Column(DateTime, nullable=False)
    cible = Column(String(20), nullable=False)
    velo_id = Column(String(50), nullable=True)
    station_id = Column(String(50), ForeignKey("station.station_id"), nullable=True)
    type_incident = Column(String(100), nullable=True)
    statut = Column(String(20), nullable=False, default="ouvert")
    date_resolution = Column(DateTime, nullable=True)
    technicien = Column(String(100), nullable=True)

    station = relationship("Station", back_populates="incidents")


class Utilisateur(Base):
    """Modèle représentant un compte utilisateur et ses droits d'accès."""

    __tablename__ = "utilisateur"

    id_utilisateur = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    mot_de_passe_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)