"""Routeur FastAPI pour l'authentification."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Utilisateur
from api.schemas import LoginRequest, TokenResponse
from api.securite import creer_jeton_acces, verifier_mot_de_passe

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authentifie un utilisateur et renvoie un jeton JWT."""
    utilisateur = (
        db.query(Utilisateur)
        .filter(Utilisateur.username == payload.username)
        .first()
    )

    if (
        utilisateur is None
        or not verifier_mot_de_passe(payload.password, utilisateur.mot_de_passe_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jeton = creer_jeton_acces(
        data={"sub": utilisateur.username, "role": utilisateur.role}
    )

    return TokenResponse(
        access_token=jeton,
        token_type="bearer",
        role=utilisateur.role,
    )