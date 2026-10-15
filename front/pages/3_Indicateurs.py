"""Écran Indicateurs.

À compléter : trois st.metric et trois tableaux issus des trois endpoints
/indicateurs. Aucun graphique.
"""
"""Écran Indicateurs.

Graphiques d'activité, top stations et statut des incidents.
"""

import pandas as pd
import streamlit as st

try:
    from front.api_client import ErreurApi, client_api
except ModuleNotFoundError:
    from api_client import ErreurApi, client_api

st.set_page_config(page_title="VéloVille - Indicateurs", page_icon="📊", layout="wide")
st.title("📊 Indicateurs et Tableaux de Bord")

token = st.session_state.get("token")
if not token:
    st.warning("⚠️ Veuillez vous connecter sur la page d'accueil pour accéder aux indicateurs.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["Activité par jour", "Top Stations Actives", "Incidents par statut"])

# Onglet 1 : Activité quotidienne
with tab1:
    st.subheader("Activité globale du réseau par jour")
    try:
        data_act = client_api.get_indicateurs_activite(token)
        if data_act:
            df_act = pd.DataFrame(data_act)
            if "date" in df_act.columns and "nombre_trajets" in df_act.columns:
                df_act["date"] = pd.to_datetime(df_act["date"])
                df_act = df_act.sort_values("date")
                st.line_chart(df_act.set_index("date")[["nombre_trajets"]])
            st.dataframe(df_act, use_container_width=True)
        else:
            st.info("Aucune donnée d'activité disponible.")
    except ErreurApi as e:
        st.error(f"Erreur indicateurs activité : {e}")

# Onglet 2 : Stations les plus actives
with tab2:
    st.subheader("Top 10 des stations les plus fréquentées")
    try:
        data_st = client_api.get_indicateurs_stations_actives(token, limite=10)
        if data_st:
            df_st = pd.DataFrame(data_st)
            col_label = "nom" if "nom" in df_st.columns else "station_id"
            col_val = "total_departs" if "total_departs" in df_st.columns else df_st.columns[-1]
            st.bar_chart(df_st.set_index(col_label)[col_val])
            st.dataframe(df_st, use_container_width=True)
        else:
            st.info("Aucune donnée de stations disponible.")
    except ErreurApi as e:
        st.error(f"Erreur indicateurs stations : {e}")

# Onglet 3 : Répartition des incidents
with tab3:
    st.subheader("Répartition des incidents par statut")
    try:
        data_inc = client_api.get_indicateurs_incidents_par_statut(token)
        if data_inc:
            df_inc = pd.DataFrame(data_inc)
            col_statut = "statut" if "statut" in df_inc.columns else df_inc.columns[0]
            col_total = "nombre" if "nombre" in df_inc.columns else df_inc.columns[1]
            st.bar_chart(df_inc.set_index(col_statut)[col_total])
            st.dataframe(df_inc, use_container_width=True)
        else:
            st.info("Aucune donnée d'incidents disponible.")
    except ErreurApi as e:
        st.error(f"Erreur indicateurs incidents : {e}")