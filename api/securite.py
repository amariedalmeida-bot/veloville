"""Authentification et autorisation.

À compléter : vérification d'un mot de passe contre son hachage bcrypt, création et
décodage du JWT (secret et algorithme lus dans l'environnement),
dépendances utilisateur_courant() et exiger_role("exploitant").
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Utilisateur

# Configuration issue de l'environnement (.env)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret-cle-veloville-epreuve-2026")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# Schéma de sécurité HTTP Bearer pour FastAPI
bearer_scheme = HTTPBearer(auto_error=False)


def hacher_mot_de_passe(mot_de_passe_clair: str) -> str:
    """Génère une empreinte bcrypt à partir d'un mot de passe en clair."""
    octets = mot_de_passe_clair.encode("utf-8")
    sel = bcrypt.gensalt()
    return bcrypt.hashpw(octets, sel).decode("utf-8")


def verifier_mot_de_passe(mot_de_passe_clair: str, mot_de_passe_hache: str) -> bool:
    """Vérifie un mot de passe en clair contre son empreinte bcrypt."""
    try:
        octets = mot_de_passe_clair.encode("utf-8")
        hache_octets = mot_de_passe_hache.encode("utf-8")
        return bcrypt.checkpw(octets, hache_octets)
    except Exception:
        return False


def creer_jeton_acces(data: dict, duree_minutes: Optional[int] = None) -> str:
    """Crée un jeton JWT signé avec une expiration."""
    a_coder = data.copy()
    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=duree_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    )
    a_coder.update({"exp": expiration})
    return jwt.encode(a_coder, SECRET_KEY, algorithm=ALGORITHM)


def utilisateur_courant(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Utilisateur:
    """Récupère l'utilisateur authentifié via son jeton Bearer (401 si absent ou invalide)."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'authentification manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jeton = credentials.credentials
    try:
        charge_utile = jwt.decode(jeton, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = charge_utile.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Jeton invalide (identifiant absent)",
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    utilisateur = db.query(Utilisateur).filter(Utilisateur.username == username).first()
    if utilisateur is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
        )
    return utilisateur


def exiger_role(*roles_autorises: str) -> Callable:
    """Fabrique une dépendance FastAPI refusant l'accès avec 403 si le rôle est insuffisant."""
    def verification_role(
        utilisateur: Utilisateur = Depends(utilisateur_courant),
    ) -> Utilisateur:
        if utilisateur.role not in roles_autorises:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé pour le rôle : {utilisateur.role}",
            )
        return utilisateur

    return verification_role