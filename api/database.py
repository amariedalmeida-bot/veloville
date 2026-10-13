"""Connexion à PostgreSQL (SQLAlchemy 2).

À compléter : lire DATABASE_URL depuis l'environnement (.env), créer l'engine, la
fabrique de sessions et la dépendance get_db() utilisée par les routeurs.
"""
"""Configuration de la connexion PostgreSQL et session SQLAlchemy."""

import os
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL non configuré dans .env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dépendance FastAPI fournissant une session SQLAlchemy par requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()