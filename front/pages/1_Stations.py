# Page de consultation des stations.

from typing import List

import pandas as pd
import streamlit as st

try:
    from front.api_client import ErreurApi, client_api
except ModuleNotFoundError:
    from api_client import ErreurApi, client_api

st.set_page_config(page_title="VéloVille - Stations", page_icon="🚲", layout="wide")
st.title("📍 Consultation des stations")


@st.cache_data(ttl=300)
def charger_communes(token: str) -> List[str]:
    """Met en cache les communes du référentiel pendant cinq minutes."""
    return client_api.get_communes_stations(token)


# Vérification de l'authentification
token = st.session_state.get("token")
if not token:
    st.warning("⚠️ Veuillez vous connecter sur la page d'accueil pour accéder aux stations.")
    st.stop()

# Filtre par commune
try:
    communes = charger_communes(token)
except ErreurApi as e:
    st.error(f"Erreur lors du chargement des communes : {e}")
    st.stop()

commune_filtre = st.selectbox(
    "Filtrer par commune",
    options=["Toutes"] + communes,
)
commune_param = None if commune_filtre == "Toutes" else commune_filtre

# Pagination
taille_page = st.selectbox(
    "Stations par page",
    options=[10, 20, 50],
    index=1,
    key="stations_taille_page",
)
criteres = (commune_param, taille_page)
if st.session_state.get("_stations_criteres") != criteres:
    st.session_state["_stations_criteres"] = criteres
    st.session_state["stations_page"] = 1
else:
    st.session_state.setdefault("stations_page", 1)

# Récupération et affichage
try:
    reponse = client_api.get_stations(
        token=token,
        page=st.session_state["stations_page"],
        taille_page=taille_page,
        commune=commune_param,
    )
    stations = reponse.get("resultats", [])
    total = reponse.get("total", 0)
    nombre_pages = max(1, (total + taille_page - 1) // taille_page)

    st.write(f"**Nombre total de stations :** {total}")

    col_precedente, col_indication, col_suivante = st.columns([1, 2, 1])
    with col_precedente:
        if st.button(
            "Page précédente",
            disabled=st.session_state["stations_page"] <= 1,
            key="stations_page_precedente",
        ):
            st.session_state["stations_page"] -= 1
            st.rerun()
    with col_indication:
        st.write(f"Page {st.session_state['stations_page']} sur {nombre_pages}")
    with col_suivante:
        if st.button(
            "Page suivante",
            disabled=st.session_state["stations_page"] >= nombre_pages,
            key="stations_page_suivante",
        ):
            st.session_state["stations_page"] += 1
            st.rerun()

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