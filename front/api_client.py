"""Client HTTP centralisé vers l'API VéloVille.

À compléter : lire API_URL et API_TIMEOUT_SECONDES, ajouter l'en-tête
Authorization: Bearer <jeton>, lever ErreurApi (message en français)
sur erreur réseau, délai dépassé ou code HTTP d'erreur.
"""
"""Client HTTP centralisé vers l'API VéloVille.

Lecture de API_URL et API_TIMEOUT_SECONDES, ajout de l'en-tête
Authorization: Bearer <jeton>, levée de ErreurApi (message en français)
sur erreur réseau, délai dépassé ou code HTTP d'erreur.
"""

import os
from typing import Any, Dict, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
API_TIMEOUT = int(os.getenv("API_TIMEOUT_SECONDES", "5"))


class ErreurApi(Exception):
    """Erreur levée lorsque l'API est injoignable ou répond en erreur."""
    pass


def requete(
    methode: str,
    chemin: str,
    token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Exécute une requête HTTP vers l'API avec gestion centralisée des erreurs."""
    url = f"{API_URL}{chemin}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        reponse = requests.request(
            method=methode,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            timeout=API_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        raise ErreurApi("Le délai d'attente de l'API a été dépassé.")
    except requests.exceptions.ConnectionError:
        raise ErreurApi(f"Impossible de joindre le serveur API sur {API_URL}.")
    except requests.exceptions.RequestException as e:
        raise ErreurApi(f"Erreur de communication avec l'API : {e}")

    if not reponse.ok:
        try:
            detail = reponse.json().get("detail", reponse.text)
        except Exception:
            detail = reponse.text

        if reponse.status_code == 401:
            raise ErreurApi("Identifiant ou mot de passe incorrect (ou session expirée).")
        if reponse.status_code == 403:
            raise ErreurApi("Accès refusé : rôle insuffisant pour effectuer cette action.")
        if reponse.status_code == 404:
            raise ErreurApi(f"Ressource introuvable : {detail}")
        raise ErreurApi(f"Erreur API ({reponse.status_code}) : {detail}")

    return reponse.json()


def login(username: str, password: str) -> Dict[str, Any]:
    """Authentification via POST /auth/login."""
    return requete("POST", "/auth/login", json_data={"username": username, "password": password})


def get_sante() -> Dict[str, Any]:
    """Vérification de l'état de l'API via GET /sante."""
    return requete("GET", "/sante")


def get_stations(token: str, page: int = 1, taille_page: int = 20) -> Dict[str, Any]:
    """Récupère la liste paginée des stations."""
    return requete("GET", "/stations", token=token, params={"page": page, "taille_page": taille_page})


def get_incidents(
    token: str,
    statut: Optional[str] = None,
    page: int = 1,
    taille_page: int = 20,
) -> Dict[str, Any]:
    """Récupère la liste paginée des incidents avec filtre éventuel."""
    params: Dict[str, Any] = {"page": page, "taille_page": taille_page}
    if statut:
        params["statut"] = statut
    return requete("GET", "/incidents", token=token, params=params)


def update_statut_incident(
    token: str,
    incident_id: str,
    nouveau_statut: str,
    technicien: Optional[str] = None,
) -> Dict[str, Any]:
    """Met à jour le statut d'un incident via PUT /incidents/{incident_id}/statut."""
    payload = {"nouveau_statut": nouveau_statut}
    if technicien:
        payload["technicien"] = technicien
    return requete("PUT", f"/incidents/{incident_id}/statut", token=token, json_data=payload)

def get_indicateurs_activite_jour(token: str, date_jour: Optional[str] = None) -> Dict[str, Any]:
    """Récupère l'indicateur d'activité journalière via GET /indicateurs/activite-par-jour."""
    params = {"date": date_jour} if date_jour else None
    return requete("GET", "/indicateurs/activite-par-jour", token=token, params=params)


def get_indicateurs_rotations(token: str) -> Dict[str, Any]:
    """Récupère les stations actives via GET /indicateurs/stations-actives."""
    return requete("GET", "/indicateurs/stations-actives", token=token)


def get_indicateurs_incidents_statut(token: str) -> Dict[str, Any]:
    """Récupère la répartition des incidents via GET /indicateurs/incidents-statut."""
    return requete("GET", "/indicateurs/incidents-statut", token=token)