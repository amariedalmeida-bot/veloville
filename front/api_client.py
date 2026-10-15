"""Client HTTP centralisé vers l'API VéloVille.

À compléter : lire API_URL et API_TIMEOUT_SECONDES, ajouter l'en-tête
Authorization: Bearer <jeton>, lever ErreurApi (message en français)
sur erreur réseau, délai dépassé ou code HTTP d'erreur.
"""

"""Client HTTP pour dialoguer avec l'API FastAPI VéloVille."""

import os
from typing import Any, Dict, List, Optional, Tuple
import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


class ErreurApi(Exception):
    """Exception levee en cas d'erreur de l'API."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    """Client pour les appels a l'API FastAPI."""

    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url.rstrip("/")

    def _headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def login(
        self, username: str, password: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Authentifie un utilisateur. Renvoie (access_token, role, erreur)."""
        url = f"{self.base_url}/auth/login"
        payload = {"username": username, "password": password}
        try:
            reponse = requests.post(url, json=payload, timeout=5)
            if reponse.status_code == 200:
                data = reponse.json()
                return data.get("access_token"), data.get("role"), None
            if reponse.status_code == 401:
                return None, None, "Identifiants invalides."
            return (
                None,
                None,
                f"Erreur HTTP {reponse.status_code} : {reponse.text}",
            )
        except requests.exceptions.RequestException as e:
            return None, None, f"Impossible de joindre l'API : {e}"

    def get_stations(
        self,
        token: Optional[str] = None,
        page: int = 1,
        taille_page: int = 20,
        commune: Optional[str] = None,
        statut: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Recupere la liste paginee des stations."""
        url = f"{self.base_url}/stations"
        params: Dict[str, Any] = {"page": page, "taille_page": taille_page}
        if commune:
            params["commune"] = commune
        if statut:
            params["statut"] = statut

        reponse = requests.get(
            url, params=params, headers=self._headers(token), timeout=5
        )
        if reponse.status_code != 200:
            raise ErreurApi(
                f"Erreur recuperation stations : {reponse.text}",
                reponse.status_code,
            )
        return reponse.json()

    def get_incidents(
        self,
        token: str,
        page: int = 1,
        taille_page: int = 20,
        statut: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Recupere la liste des incidents."""
        url = f"{self.base_url}/incidents"
        params: Dict[str, Any] = {"page": page, "taille_page": taille_page}
        if statut:
            params["statut"] = statut

        reponse = requests.get(
            url, params=params, headers=self._headers(token), timeout=5
        )
        if reponse.status_code != 200:
            raise ErreurApi(
                f"Erreur recuperation incidents : {reponse.text}",
                reponse.status_code,
            )
        return reponse.json()

    def modifier_statut_incident(
        self, token: str, incident_id: str, nouveau_statut: str
    ) -> Dict[str, Any]:
        """Modifie le statut d'un incident."""
        url = f"{self.base_url}/incidents/{incident_id}/statut"
        payload = {"statut": nouveau_statut}
        reponse = requests.put(
            url, json=payload, headers=self._headers(token), timeout=5
        )
        if reponse.status_code != 200:
            raise ErreurApi(
                f"Erreur modification statut : {reponse.text}",
                reponse.status_code,
            )
        return reponse.json()

    def get_indicateurs_activite(
        self,
        token: str,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Recupere l'activite par jour."""
        url = f"{self.base_url}/indicateurs/activite-par-jour"
        params = {}
        if date_debut:
            params["date_debut"] = date_debut
        if date_fin:
            params["date_fin"] = date_fin

        reponse = requests.get(
            url, params=params, headers=self._headers(token), timeout=5
        )
        if reponse.status_code != 200:
            raise ErreurApi(
                f"Erreur indicateurs activite : {reponse.text}",
                reponse.status_code,
            )
        return reponse.json()

    def get_indicateurs_stations_actives(
        self, token: str, limite: int = 10
    ) -> List[Dict[str, Any]]:
        """Recupere le top des stations actives."""
        url = f"{self.base_url}/indicateurs/stations-actives"
        reponse = requests.get(
            url,
            params={"limite": limite},
            headers=self._headers(token),
            timeout=5,
        )
        if reponse.status_code != 200:
            raise ErreurApi(
                f"Erreur indicateurs stations : {reponse.text}",
                reponse.status_code,
            )
        return reponse.json()

    def get_indicateurs_incidents_par_statut(
        self, token: str
    ) -> List[Dict[str, Any]]:
        """Recupere la repartition des incidents par statut."""
        url = f"{self.base_url}/indicateurs/incidents-par-statut"
        reponse = requests.get(url, headers=self._headers(token), timeout=5)
        if reponse.status_code != 200:
            raise ErreurApi(
                f"Erreur indicateurs incidents : {reponse.text}",
                reponse.status_code,
            )
        return reponse.json()


client_api = ApiClient()