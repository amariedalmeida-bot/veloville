"""Connexion à PostgreSQL (SQLAlchemy 2).

À compléter : lire DATABASE_URL depuis l'environnement (.env), créer l'engine, la
fabrique de sessions et la dépendance get_db() utilisée par les routeurs.
"""
import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{ROOT_DIR / 'veloville.db'}"
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Generateur de session injecte via Depends(get_db)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()