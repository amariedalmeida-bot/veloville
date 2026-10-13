"""Authentification et autorisation.

À compléter : vérification d'un mot de passe contre son hachage bcrypt, création et
décodage du JWT (secret et algorithme lus dans l'environnement),
dépendances utilisateur_courant() et exiger_role("exploitant").
"""
"""Authentification et autorisation."""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

JWT_SECRET = os.getenv("JWT_SECRET", "cle_par_defaut_insecure")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))


def verifier_mot_de_passe(mot_de_passe: str, mot_de_passe_hash: str) -> bool:
    """Vérifie un mot de passe en clair contre son empreinte bcrypt."""
    return bcrypt.checkpw(mot_de_passe.encode("utf-8"), mot_de_passe_hash.encode("utf-8"))


def creer_jeton_jwt(donnees: Dict[str, Any], duree_minutes: Optional[int] = None) -> str:
    """Crée un jeton d'accès JWT signé."""
    a_encoder = donnees.copy()
    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=duree_minutes or JWT_EXPIRATION_MINUTES
    )
    a_encoder.update({"exp": expiration})
    return jwt.encode(a_encoder, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decoder_jeton_jwt(jeton: str) -> Dict[str, Any]:
    """Décode et valide un jeton JWT."""
    try:
        payload = jwt.decode(jeton, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )


def utilisateur_courant(
    jeton: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Dépendance FastAPI injectant l'utilisateur authentifié depuis le jeton."""
    payload = decoder_jeton_jwt(jeton)
    username: Optional[str] = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton sans identifiant utilisateur",
            headers={"WWW-Authenticate": "Bearer"},
        )

    requete = text(
        "SELECT id_utilisateur, username, role FROM utilisateur WHERE username = :username"
    )
    resultat = db.execute(requete, {"username": username}).mappings().first()

    if not resultat:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return dict(resultat)


def exiger_role(role_requis: str):
    """Vérifie que l'utilisateur courant possède le rôle exigé."""
    def dependance_role(utilisateur: Dict[str, Any] = Depends(utilisateur_courant)) -> Dict[str, Any]:
        if utilisateur.get("role") != role_requis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action réservée au rôle : {role_requis}",
            )
        return utilisateur

    return dependance_role