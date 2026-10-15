"""Écran Stations.

À compléter : tableau des stations filtrable par commune, pagination.
"""
"""Écran Stations.

Tableau des stations filtrable par commune, statut, avec pagination.
"""
"""Écran Stations.

Tableau des stations filtrable par commune, statut, avec pagination.
"""

import pandas as pd
import streamlit as st

try:
    from front.api_client import ErreurApi, client_api
except ModuleNotFoundError:
    from api_client import ErreurApi, client_api

st.set_page_config(page_title="VéloVille - Stations", page_icon="🚲", layout="wide")
st.title("📍 Consultation des stations")

# Vérification de l'authentification
token = st.session_state.get("token")
if not token:
    st.warning("⚠️ Veuillez vous connecter sur la page d'accueil pour accéder aux stations.")
    st.stop()

# Filtres
col1, col2 = st.columns(2)
with col1:
    commune_filtre = st.text_input("Filtrer par commune", value="")
with col2:
    statut_filtre = st.selectbox(
        "Filtrer par statut",
        options=["Tous", "EN_SERVICE", "MAINTENANCE", "HORS_SERVICE"],
    )

statut_param = None if statut_filtre == "Tous" else statut_filtre
commune_param = commune_filtre.strip() if commune_filtre.strip() else None

# Récupération et affichage
try:
    reponse = client_api.get_stations(
        token=token,
        page=1,
        taille_page=100,
        commune=commune_param,
        statut=statut_param,
    )
    stations = reponse.get("items", [])
    total = reponse.get("total", 0)

    st.write(f"**Nombre total de stations :** {total}")

    if stations:
        df = pd.DataFrame(stations)
        colonnes_affichees = [
            col for col in ["station_id", "nom", "commune", "capacite", "statut", "latitude", "longitude"]
            if col in df.columns
        ]
        st.dataframe(df[colonnes_affichees] if colonnes_affichees else df, use_container_width=True)
    else:
        st.info("Aucune station ne correspond à vos filtres.")

except ErreurApi as e:
    st.error(f"Erreur lors de la récupération des stations : {e}")