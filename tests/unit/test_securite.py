import importlib

import pytest

from api import securite


def test_secret_jwt_obligatoire(monkeypatch):
    secret_initial = securite.SECRET_KEY

    with monkeypatch.context() as environnement:
        environnement.delenv("JWT_SECRET", raising=False)
        environnement.delenv("JWT_SECRET_KEY", raising=False)
        with pytest.raises(RuntimeError, match="JWT_SECRET"):
            importlib.reload(securite)

        environnement.setenv("JWT_SECRET", secret_initial)
        importlib.reload(securite)


def test_duree_jwt_lue_depuis_variable_documentee(monkeypatch):
    secret_initial = securite.SECRET_KEY
    duree_initiale = securite.ACCESS_TOKEN_EXPIRE_MINUTES

    with monkeypatch.context() as environnement:
        environnement.setenv("JWT_SECRET", secret_initial)
        environnement.setenv("JWT_EXPIRATION_MINUTES", "17")
        importlib.reload(securite)
        assert securite.ACCESS_TOKEN_EXPIRE_MINUTES == 17

        environnement.setenv("JWT_EXPIRATION_MINUTES", str(duree_initiale))
        importlib.reload(securite)
