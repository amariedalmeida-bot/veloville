"""Client HTTP centralise pour l'interface Streamlit."""

from datetime import date
import os
from typing import Any, Dict, List, Optional, Tuple
import httpx


class ErreurApi(Exception):
    """Exception levee en cas d'erreur de communication avec l'API."""

    def __init__(self, message: str, code_statut: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.code_statut = code_statut

    def __str__(self) -> str:
        return self.message


class ApiClient:
    """Client pour interagir avec les endpoints de l'API VeloVille."""

    def __init__(self, url_base: Optional[str] = None):
        self.url_base = (
            url_base or os.getenv("API_URL") or "http://127.0.0.1:8000"
        ).rstrip("/")

    def _headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def login(self, nom_utilisateur: str, mot_de_passe: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Authentifie un utilisateur et retourne (token, role, message_erreur)."""
        url = f"{self.url_base}/auth/login"
        payload = {"username": nom_utilisateur, "password": mot_de_passe}

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    token = data.get("access_token") or data.get("jeton")
                    role = data.get("role") or "exploitant"
                    return token, role, None
                elif res.status_code in (400, 401):
                    return None, None, "Identifiant ou mot de passe incorrect."
                else:
                    return None, None, f"Erreur serveur ({res.status_code}) : {res.text}"
        except httpx.RequestError:
            return None, None, "Impossible de joindre le serveur API. Verifiez qu'Uvicorn est demarre."

    def get_stations(
        self,
        token: str,
        page: int = 1,
        taille_page: int = 20,
        commune: Optional[str] = None,
        statut: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.url_base}/stations"
        params: Dict[str, Any] = {"page": page, "taille_page": taille_page}
        if commune:
            params["commune"] = commune
        if statut:
            params["statut"] = statut

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, params=params, headers=self._headers(token))
                if res.status_code == 200:
                    return res.json()
                raise ErreurApi(f"Erreur recuperation stations ({res.status_code}).", res.status_code)
        except httpx.RequestError as exc:
            raise ErreurApi(f"Impossible de joindre l'API : {exc}")

    def get_communes_stations(self, token: str) -> List[str]:
        url = f"{self.url_base}/stations/communes"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, headers=self._headers(token))
                if res.status_code == 200:
                    return res.json()
                raise ErreurApi(f"Erreur recuperation communes ({res.status_code}).", res.status_code)
        except httpx.RequestError as exc:
            raise ErreurApi(f"Impossible de joindre l'API : {exc}")

    def get_incidents(
        self,
        token: str,
        page: int = 1,
        taille_page: int = 20,
        statut: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.url_base}/incidents"
        params: Dict[str, Any] = {"page": page, "taille_page": taille_page}
        if statut:
            params["statut"] = statut

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, params=params, headers=self._headers(token))
                if res.status_code == 200:
                    return res.json()
                raise ErreurApi(f"Erreur recuperation incidents ({res.status_code}).", res.status_code)
        except httpx.RequestError as exc:
            raise ErreurApi(f"Impossible de joindre l'API : {exc}")

    def modifier_statut_incident(
        self,
        token: str,
        incident_id: str,
        nouveau_statut: str,
    ) -> Dict[str, Any]:
        url = f"{self.url_base}/incidents/{incident_id}/statut"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.put(url, json={"statut": nouveau_statut}, headers=self._headers(token))
                if res.status_code == 200:
                    return res.json()
                elif res.status_code == 403:
                    raise ErreurApi("Action interdite : seul le profil exploitant peut modifier un statut.", 403)
                raise ErreurApi(f"Erreur mise a jour incident ({res.status_code}).", res.status_code)
        except httpx.RequestError as exc:
            raise ErreurApi(f"Impossible de joindre l'API : {exc}")

    def get_indicateurs_activite(
        self,
        token: str,
        date_debut: Optional[date] = None,
        date_fin: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        url = f"{self.url_base}/indicateurs/activite-par-jour"
        params = {}
        if date_debut:
            params["date_debut"] = str(date_debut)
        if date_fin:
            params["date_fin"] = str(date_fin)

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(url, params=params, headers=self._headers(token))
                if res.status_code == 200:
                    return res.json()
                raise ErreurApi(f"Erreur indicateurs activite ({res.status_code})", res.status_code)
        except httpx.RequestError as exc:
            raise ErreurApi(f"Impossible de joindre l'API : {exc}")

    def get_indicateurs_stations(
        self,
        token: str,
        limite: int = 10,
    ) -> List[Dict[str, Any]]:
        url = f"{self.url_base}/indicateurs/stations-actives"
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(url, params={"limite": limite}, headers=self._headers(token))
                if res.status_code == 200:
                    return res.json()
                raise ErreurApi(f"Erreur indicateurs stations ({res.status_code})", res.status_code)
        except httpx.RequestError as exc:
            raise ErreurApi(f"Impossible de joindre l'API : {exc}")

    def get_indicateurs_incidents(
        self,
        token: str,
    ) -> List[Dict[str, Any]]:
        url = f"{self.url_base}/indicateurs/incidents-par-statut"
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(url, headers=self._headers(token))
                if res.status_code == 200:
                    return res.json()
                raise ErreurApi(f"Erreur indicateurs incidents ({res.status_code})", res.status_code)
        except httpx.RequestError as exc:
            raise ErreurApi(f"Impossible de joindre l'API : {exc}")


client_api = ApiClient()
