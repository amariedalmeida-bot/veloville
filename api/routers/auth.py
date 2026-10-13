"""Routeur auth.

À compléter : POST /auth/login.
"""

"""Routeur auth.

Gestion de la connexion et de la génération des jetons JWT.
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.database import get_db
from api.securite import creer_jeton_jwt, verifier_mot_de_passe

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginPayload(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


def _authentifier_utilisateur(db: Session, username: str, mot_de_passe: str) -> Dict[str, Any]:
    requete = text(
        "SELECT id_utilisateur, username, mot_de_passe_hash, role FROM utilisateur WHERE username = :username"
    )
    utilisateur = db.execute(requete, {"username": username}).mappings().first()

    if not utilisateur or not verifier_mot_de_passe(mot_de_passe, utilisateur["mot_de_passe_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    donnees_token = {
        "sub": utilisateur["username"],
        "role": utilisateur["role"],
    }
    jeton = creer_jeton_jwt(donnees_token)

    return {
        "access_token": jeton,
        "token_type": "bearer",
        "role": utilisateur["role"],
        "username": utilisateur["username"],
    }


@router.post("/token", response_model=TokenResponse)
def login_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Route compatible OAuth2 / Swagger UI."""
    return _authentifier_utilisateur(db, form_data.username, form_data.password)


@router.post("/login", response_model=TokenResponse)
def login_json(
    payload: LoginPayload,
    db: Session = Depends(get_db),
):
    """Route JSON pour le front-end Streamlit / requêtes clientes."""
    return _authentifier_utilisateur(db, payload.username, payload.password)
