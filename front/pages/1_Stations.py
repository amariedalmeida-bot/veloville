"""Écran Stations.

À compléter : tableau des stations filtrable par commune, pagination.
"""

import streamlit as st
import pandas as pd
from api_client import get_stations, ErreurApi

st.set_page_config(page_title="VéloVille - Stations", page_icon="🚲", layout="wide")

st.title("📍 Gestion des stations")

# Vérification de l'authentification
token = st.session_state.get("token")
if not token:
    st.warning("Veuillez vous connecter depuis la page d'accueil pour accéder aux stations.")
    st.stop()

# Barre de contrôle : pagination et filtres
col1, col2 = st.columns([1, 2])

with col1:
    page = st.number_input("Page", min_value=1, value=1, step=1)
with col2:
    taille_page = st.selectbox("Nombre de stations par page", options=[10, 20, 50, 100], index=1)

# Récupération des données depuis l'API
try:
    reponse = get_stations(token=token, page=page, taille_page=taille_page)
    stations = reponse.get("stations", [])
    total = reponse.get("total", len(stations))
except ErreurApi as e:
    st.error(f"Erreur lors de la récupération des stations : {e}")
    st.stop()

if not stations:
    st.info("Aucune station trouvée pour cette page.")
else:
    df = pd.DataFrame(stations)

    # Filtre optionnel par commune sur les résultats récupérés
    communes_disponibles = sorted([c for c in df["commune"].dropna().unique() if c])
    filtre_commune = st.multiselect("Filtrer par commune :", options=communes_disponibles)

    if filtre_commune:
        df = df[df["commune"].isin(filtre_commune)]

    st.caption(f"Affichage de {len(df)} station(s) sur un total estimé de {total} stations.")

    # Affichage du tableau formaté
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "station_id": "Identifiant",
            "nom": "Nom de la station",
            "commune": "Commune",
            "capacite": st.column_config.NumberColumn("Capacité", format="%d"),
            "latitude": st.column_config.NumberColumn("Latitude", format="%.5f"),
            "longitude": st.column_config.NumberColumn("Longitude", format="%.5f"),
            "date_mise_en_service": "Mise en service",
        },
    )