import subprocess
from pathlib import Path

import pytest

from scripts import sauvegarde


def test_configuration_postgresql_transmise_sans_url_ni_cle_jwt(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://veloville:secret%40prive@localhost:5433/veloville",
    )
    monkeypatch.setenv("JWT_SECRET", "cle-privee")

    url, environnement = sauvegarde.charger_configuration()

    assert url.database == "veloville"
    assert environnement["PGHOST"] == "localhost"
    assert environnement["PGPORT"] == "5433"
    assert environnement["PGUSER"] == "veloville"
    assert environnement["PGPASSWORD"] == "secret@prive"
    assert environnement["PGDATABASE"] == "veloville"
    assert "DATABASE_URL" not in environnement
    assert "JWT_SECRET" not in environnement


def test_configuration_refuse_une_base_non_postgresql(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///veloville.db")

    with pytest.raises(RuntimeError, match="PostgreSQL"):
        sauvegarde.charger_configuration()


def test_sauvegarde_cree_une_archive_custom(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://veloville:secret@localhost/veloville"
    )
    monkeypatch.setattr(sauvegarde.shutil, "which", lambda _: "pg_dump")
    appels = {}

    def simuler_pg_dump(arguments, **options):
        appels["arguments"] = arguments
        appels["options"] = options
        archive = Path(arguments[arguments.index("--file") + 1])
        archive.write_bytes(b"archive de test")
        return subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr(sauvegarde.subprocess, "run", simuler_pg_dump)

    archive = sauvegarde.sauvegarder(tmp_path)

    assert archive.parent == tmp_path
    assert archive.read_bytes() == b"archive de test"
    assert "--format=custom" in appels["arguments"]
    assert appels["options"]["env"]["PGPASSWORD"] == "secret"
    assert "DATABASE_URL" not in appels["options"]["env"]


def test_restauration_exige_une_confirmation(tmp_path):
    with pytest.raises(ValueError, match="--confirmer"):
        sauvegarde.restaurer(tmp_path / "absence.dump")
