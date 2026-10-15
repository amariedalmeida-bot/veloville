"""Schémas Pydantic (entrées et sorties de l'API).

À compléter : schémas de lecture des trois ressources, enveloppe paginée, corps de
connexion, réponse de connexion, corps de changement de statut, réponses
des trois indicateurs.
"""
from datetime import date, datetime
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# --- ENVELOPPE PAGINEE GENERIQUE ---
class PageReponse(BaseModel, Generic[T]):
    total: int = Field(..., description="Nombre total d'elements correspondant au filtre")
    page: int = Field(..., description="Numero de la page courante (>= 1)")
    taille_page: int = Field(..., description="Nombre d'elements par page (1 a 100)")
    resultats: List[T] = Field(..., description="Elements de la page courante")


# --- AUTHENTIFICATION ---
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Nom d'utilisateur")
    password: str = Field(..., min_length=1, description="Mot de passe en clair")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


# --- STATIONS ---
class StationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    station_id: str
    nom: str
    commune: str
    capacite: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    date_mise_en_service: Optional[date] = None


# --- TRAJETS ---
class TrajetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trajet_id: str
    velo_id: Optional[str] = None
    depart_horodatage: datetime
    station_depart: str
    station_arrivee: Optional[str] = None
    duree_secondes: int
    type_usager: Optional[str] = None
    usager_ref: Optional[str] = None


# --- INCIDENTS ---
class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident_id: str
    date_signalement: datetime
    cible: str
    velo_id: Optional[str] = None
    station_id: Optional[str] = None
    type_incident: Optional[str] = None
    statut: str
    date_resolution: Optional[datetime] = None
    
class IncidentStatutUpdate(BaseModel):
    statut: str = Field(
        ...,
        pattern="^(ouvert|en_cours|resolu)$",
        description="Nouveau statut : 'ouvert', 'en_cours' ou 'resolu'",
    )


# --- INDICATEURS METIER ---
class ActiviteJour(BaseModel):
    date: date
    nb_trajets: int
    duree_moyenne_secondes: float


class StationActive(BaseModel):
    station_id: str
    nom: str
    commune: str
    nb_departs: int
    nb_arrivees: int
    total_trajets: int


class IncidentStatut(BaseModel):
    statut: str
    nb_incidents: int
    delai_moyen_heures: Optional[float] = None
    
IncidentRead.model_rebuild()    