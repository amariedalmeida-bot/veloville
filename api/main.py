"""Point d'entrée de l'API VéloVille (FastAPI).

À compléter : créer l'application, inclure les routeurs (auth, stations, trajets,
incidents, indicateurs) et exposer GET /sante -> {"statut": "ok"}.

Lancement : uvicorn api.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import auth, incidents, indicateurs, stations, trajets

app = FastAPI(
    title="VéloVille API",
    description="API de gestion et d'exploitation du réseau VéloVille",
    version="1.0.0",
)

# Configuration CORS pour autoriser les requêtes du front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routeurs par ressource
app.include_router(auth.router)
app.include_router(stations.router)
app.include_router(trajets.router)
app.include_router(incidents.router)
app.include_router(indicateurs.router)


@app.get("/sante", tags=["Santé"])
def verifier_sante():
    """Vérification de l'état de l'API."""
    return {"statut": "ok"}