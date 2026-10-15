"""Sauvegarde et restauration explicites de la base PostgreSQL VéloVille."""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "sauvegardes"
load_dotenv(BASE_DIR / ".env")


def charger_configuration() -> tuple[URL, dict[str, str]]:
    """Parse DATABASE_URL et prépare l'environnement attendu par libpq."""
    chaine_url = os.getenv("DATABASE_URL")
    if not chaine_url:
        raise RuntimeError("La variable DATABASE_URL doit être renseignée dans .env.")

    try:
        url = make_url(chaine_url)
    except ArgumentError as exc:
        raise RuntimeError("La variable DATABASE_URL n'est pas une URL valide.") from exc

    if url.get_backend_name() != "postgresql" or not url.database:
        raise RuntimeError("DATABASE_URL doit désigner une base PostgreSQL.")

    environnement = os.environ.copy()
    environnement.pop("DATABASE_URL", None)
    environnement.pop("JWT_SECRET", None)
    environnement.pop("JWT_SECRET_KEY", None)
    environnement["PGDATABASE"] = url.database

    if url.host:
        environnement["PGHOST"] = url.host
    if url.port:
        environnement["PGPORT"] = str(url.port)
    if url.username:
        environnement["PGUSER"] = url.username
    if url.password is not None:
        environnement["PGPASSWORD"] = url.password
    if isinstance(url.query.get("sslmode"), str):
        environnement["PGSSLMODE"] = url.query["sslmode"]

    return url, environnement


def executer_outil_postgres(
    nom_outil: str,
    arguments: list[str],
    environnement: dict[str, str],
) -> None:
    executable = shutil.which(nom_outil)
    if executable is None:
        raise RuntimeError(
            f"{nom_outil} est introuvable. Installez les outils client PostgreSQL."
        )

    try:
        resultat = subprocess.run(
            [executable, *arguments],
            env=environnement,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError(f"Impossible de démarrer {nom_outil}.") from exc

    if resultat.returncode != 0:
        details = resultat.stderr.strip()
        message = f"{nom_outil} a échoué (code {resultat.returncode})."
        if details:
            message = f"{message} {details}"
        raise RuntimeError(message)


def sauvegarder(repertoire: Optional[Path] = None) -> Path:
    """Crée une archive PostgreSQL horodatée au format custom."""
    _, environnement = charger_configuration()
    outil = shutil.which("pg_dump")
    if outil is None:
        raise RuntimeError(
            "pg_dump est introuvable. Installez les outils client PostgreSQL."
        )

    dossier = repertoire or BACKUP_DIR
    dossier.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = dossier / f"veloville_{horodatage}.dump"
    if archive.exists():
        horodatage = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        archive = dossier / f"veloville_{horodatage}.dump"

    try:
        executer_outil_postgres(
            "pg_dump",
            ["--format=custom", "--file", str(archive)],
            environnement,
        )
    except RuntimeError:
        archive.unlink(missing_ok=True)
        raise

    if os.name != "nt":
        archive.chmod(0o600)

    print(f"Sauvegarde créée : {archive}")
    return archive


def restaurer(archive: Path, confirmer: bool = False) -> None:
    """Restaure une archive dans la base configurée ; opération destructive."""
    if not confirmer:
        raise ValueError("La restauration exige l'option explicite --confirmer.")
    if not archive.is_file():
        raise FileNotFoundError(f"Archive introuvable : {archive}")

    url, environnement = charger_configuration()
    executer_outil_postgres(
        "pg_restore",
        [
            "--clean",
            "--if-exists",
            "--no-owner",
            "--exit-on-error",
            "--dbname",
            url.database,
            str(archive.resolve()),
        ],
        environnement,
    )
    print(f"Restauration terminée dans la base {url.database}.")


def main(arguments: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--restaurer",
        type=Path,
        metavar="ARCHIVE",
        help="restaure l'archive indiquée dans DATABASE_URL",
    )
    parser.add_argument(
        "--confirmer",
        action="store_true",
        help="confirme explicitement l'opération destructive de restauration",
    )
    options = parser.parse_args(arguments)

    if options.restaurer is None and options.confirmer:
        parser.error("--confirmer ne s'utilise qu'avec --restaurer.")

    try:
        if options.restaurer is None:
            sauvegarder()
        else:
            restaurer(options.restaurer, confirmer=options.confirmer)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
