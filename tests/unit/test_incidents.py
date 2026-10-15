from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from api.database import Base
from api.models import Incident
from api.routers import incidents as routeur_incidents
from api.schemas import IncidentStatutUpdate
from api.services.incidents import (
    TransitionStatutInvalide,
    mettre_a_jour_statut_incident,
)


@pytest.fixture
def session_incidents():
    moteur = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(moteur)
    session = Session(moteur)
    try:
        yield session
    finally:
        session.close()
        moteur.dispose()


@pytest.mark.parametrize(
    ("statut_initial", "nouveau_statut"),
    [
        ("ouvert", "en_cours"),
        ("ouvert", "resolu"),
        ("en_cours", "resolu"),
    ],
)
def test_transitions_autorisees_et_date_resolution(
    session_incidents, statut_initial, nouveau_statut
):
    date_signalement = datetime.now() - timedelta(days=1)
    incident = Incident(
        incident_id="INC-TEST",
        date_signalement=date_signalement,
        cible="velo",
        velo_id="V-TEST",
        statut=statut_initial,
    )
    session_incidents.add(incident)
    session_incidents.commit()

    resultat = mettre_a_jour_statut_incident(
        session_incidents,
        incident_id=incident.incident_id,
        nouveau_statut=nouveau_statut,
    )

    assert resultat is incident
    assert resultat.statut == nouveau_statut
    if nouveau_statut == "resolu":
        assert resultat.date_resolution is not None
        assert resultat.date_resolution >= date_signalement
    else:
        assert resultat.date_resolution is None


@pytest.mark.parametrize(
    ("statut_initial", "nouveau_statut"),
    [
        ("ouvert", "ouvert"),
        ("en_cours", "ouvert"),
        ("en_cours", "en_cours"),
        ("resolu", "en_cours"),
        ("resolu", "resolu"),
    ],
)
def test_transitions_interdites_ne_modifient_pas_l_incident(
    session_incidents, statut_initial, nouveau_statut
):
    incident = Incident(
        incident_id="INC-TEST",
        date_signalement=datetime.now() - timedelta(days=1),
        cible="velo",
        velo_id="V-TEST",
        statut=statut_initial,
    )
    session_incidents.add(incident)
    session_incidents.commit()

    with pytest.raises(TransitionStatutInvalide):
        mettre_a_jour_statut_incident(
            session_incidents,
            incident_id=incident.incident_id,
            nouveau_statut=nouveau_statut,
        )

    session_incidents.refresh(incident)
    assert incident.statut == statut_initial
    assert incident.date_resolution is None


def test_resolution_refusee_si_signalement_dans_le_futur(session_incidents):
    incident = Incident(
        incident_id="INC-TEST",
        date_signalement=datetime.now() + timedelta(days=1),
        cible="velo",
        velo_id="V-TEST",
        statut="ouvert",
    )
    session_incidents.add(incident)
    session_incidents.commit()

    with pytest.raises(TransitionStatutInvalide):
        mettre_a_jour_statut_incident(
            session_incidents,
            incident_id=incident.incident_id,
            nouveau_statut="resolu",
        )

    session_incidents.refresh(incident)
    assert incident.statut == "ouvert"
    assert incident.date_resolution is None


def test_route_retourne_409_pour_transition_interdite(monkeypatch):
    def refuser_transition(**kwargs):
        raise TransitionStatutInvalide(kwargs["incident_id"])

    monkeypatch.setattr(
        routeur_incidents,
        "mettre_a_jour_statut_incident",
        refuser_transition,
    )

    with pytest.raises(HTTPException) as erreur:
        routeur_incidents.modifier_statut(
            incident_id="INC-TEST",
            payload=IncidentStatutUpdate(statut="resolu"),
            db=MagicMock(),
            _user=MagicMock(),
        )

    assert erreur.value.status_code == 409
