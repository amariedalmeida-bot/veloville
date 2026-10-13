# """Écran Indicateurs.

# À compléter : trois st.metric et trois tableaux issus des trois endpoints
# /indicateurs. Aucun graphique.
# """
import streamlit as st
import pandas as pd
from api_client import (
    get_indicateurs_activite_jour,
    get_indicateurs_rotations,
    get_indicateurs_incidents_statut,
    ErreurApi,
)

st.set_page_config(page_title="VéloVille - Indicateurs", page_icon="📊", layout="wide")

st.title("📊 Indicateurs d'activité et de performance")

token = st.session_state.get("token")
if not token:
    st.warning("Veuillez vous connecter depuis la page d'accueil pour accéder aux indicateurs.")
    st.stop()

try:
    data_activite = get_indicateurs_activite_jour(token=token)
    data_stations = get_indicateurs_rotations(token=token)
    data_incidents = get_indicateurs_incidents_statut(token=token)
except ErreurApi as e:
    st.error(f"Erreur lors de la récupération des indicateurs : {e}")
    st.stop()

# 1. Calculs pour les 3 st.metric
total_trajets = sum(item.get("total_trajets", 0) for item in data_activite) if isinstance(data_activite, list) else 0

total_mouvements_top = sum(item.get("total_mouvements", 0) for item in data_stations) if isinstance(data_stations, list) else 0

repartition = data_incidents.get("repartition", {}) if isinstance(data_incidents, dict) else {}
incidents_non_resolus = repartition.get("ouvert", 0) + repartition.get("en_cours", 0)
delai_moyen = data_incidents.get("delai_moyen_resolution_heures") if isinstance(data_incidents, dict) else None

# Affichage des 3 st.metric
st.subheader("Synthèse clé")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="Total des trajets enregistrés", value=f"{total_trajets:,}".replace(",", " "))
with m2:
    delai_txt = f"{delai_moyen:.1f} h" if delai_moyen is not None else "N/A"
    st.metric(label="Délai moyen de résolution", value=delai_txt)
with m3:
    st.metric(label="Incidents non résolus", value=incidents_non_resolus)

st.divider()

# 2. Les 3 tableaux
st.subheader("1. Activité par jour (F7)")
if data_activite:
    df_act = pd.DataFrame(data_activite)
    st.dataframe(
        df_act,
        use_container_width=True,
        hide_index=True,
        column_config={
            "jour": "Date",
            "total_trajets": st.column_config.NumberColumn("Nombre de trajets", format="%d"),
        },
    )
else:
    st.info("Aucune donnée d'activité journalière.")

st.subheader("2. Stations les plus actives (F8)")
if data_stations:
    df_st = pd.DataFrame(data_stations)
    st.dataframe(
        df_st,
        use_container_width=True,
        hide_index=True,
        column_config={
            "station_id": "Identifiant",
            "nom": "Nom de la station",
            "commune": "Commune",
            "total_departs": st.column_config.NumberColumn("Départs", format="%d"),
            "total_arrivees": st.column_config.NumberColumn("Arrivées", format="%d"),
            "total_mouvements": st.column_config.NumberColumn("Total mouvements", format="%d"),
        },
    )
else:
    st.info("Aucune station active trouvée.")

st.subheader("3. Répartition des incidents par statut (F9)")
if repartition:
    df_inc = pd.DataFrame(list(repartition.items()), columns=["Statut", "Nombre d'incidents"])
    st.dataframe(df_inc, use_container_width=True, hide_index=True)
else:
    st.info("Aucun incident enregistré.")