"""Fixtures pytest communes.

À compléter : client TestClient de l'API, jetons pour exploitant01 et direction01,
session de base de données de test. Aucun secret en dur : lire .env.
"""
"""Fixtures pytest communes pour les tests d'API."""

import pytest
from fastapi.testclient import TestClient

from api.database import SessionLocal
from api.main import app
from api.securite import creer_jeton_acces


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Client HTTP de test FastAPI."""
    return TestClient(app)


@pytest.fixture(scope="session")
def db_session():
    """Session de base de donnees pour les tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def token_exploitant() -> str:
    """Jeton JWT pour exploitant."""
    return creer_jeton_acces(data={"sub": "exploitant01", "role": "exploitant"})


@pytest.fixture(scope="session")
def token_direction() -> str:
    """Jeton JWT pour direction."""
    return creer_jeton_acces(data={"sub": "direction01", "role": "direction"})


@pytest.fixture(scope="session")
def headers_exploitant(token_exploitant: str) -> dict:
    """En-tetes HTTP d'autorisation pour exploitant."""
    return {"Authorization": f"Bearer {token_exploitant}"}


@pytest.fixture(scope="session")
def headers_direction(token_direction: str) -> dict:
    """En-tetes HTTP d'autorisation pour direction."""
    return {"Authorization": f"Bearer {token_direction}"}