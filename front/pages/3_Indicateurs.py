"""Ecran Indicateurs et tableaux de bord metiers.

Conformement a ressources/maquettes-ecrans.md :
Trois st.metric synthetiques en haut de page et trois tableaux issus
des trois endpoints /indicateurs. Aucun graphique.
"""

from datetime import date
import pandas as pd
import streamlit as st

try:
    from front.api_client import ErreurApi, client_api
except ModuleNotFoundError:
    from api_client import ErreurApi, client_api

st.set_page_config(page_title="VeloVille - Indicateurs", page_icon="📊", layout="wide")
st.title("📊 Indicateurs et Tableaux de Bord")

token = st.session_state.get("token")
if not token:
    st.warning("Veuillez vous connecter sur la page d'accueil pour acceder aux indicateurs.")
    st.stop()

# --- Recuperation des donnees des indicateurs ---
activite_data = []
stations_data = []
incidents_data = []

with st.spinner("Chargement des indicateurs en cours..."):
    try:
        activite_data = client_api.get_indicateurs_activite(token)
    except Exception as err:
        st.error(f"Erreur lors de la recuperation de l'activite : {err}")

    try:
        stations_data = client_api.get_indicateurs_stations(token, limite=10)
    except Exception as err:
        st.error(f"Erreur lors de la recuperation des stations actives : {err}")

    try:
        incidents_data = client_api.get_indicateurs_incidents(token)
    except Exception as err:
        st.error(f"Erreur lors de la recuperation des incidents : {err}")

# --- Section 1 : Trois st.metric en synthese ---
col1, col2, col3 = st.columns(3)

total_trajets_enregistres = sum(
    int(item.get("nombre_trajets") or item.get("nb_trajets") or item.get("total_trajets") or 0)
    for item in activite_data
)
station_top = stations_data[0]["nom"] if stations_data else "Aucune"
incidents_en_cours = sum(
    int(item.get("nb_incidents", 0))
    for item in incidents_data
    if str(item.get("statut", "")).lower() in ["ouvert", "en_cours"]
)

with col1:
    st.metric(label="Total des trajets enregistres", value=f"{total_trajets_enregistres:,}".replace(",", " "))
with col2:
    st.metric(label="Station la plus frequentee", value=station_top)
with col3:
    st.metric(label="Incidents non resolus", value=incidents_en_cours)

st.markdown("---")

# --- Section 2 : Trois tableaux detailles sans graphique ---
tab1, tab2, tab3 = st.tabs(["Activite par jour", "Top 10 Stations actives", "Incidents par statut"])

# Onglet 1 : Activite journaliere
with tab1:
    st.subheader("Activite journaliere du reseau")
    
    c_debut, c_fin, _ = st.columns([2, 2, 4])
    with c_debut:
        f_debut = st.date_input("Date de debut", value=None, key="act_date_debut")
    with c_fin:
        f_fin = st.date_input("Date de fin", value=None, key="act_date_fin")

    donnees_affichables = activite_data
    if f_debut or f_fin:
        try:
            donnees_affichables = client_api.get_indicateurs_activite(token, date_debut=f_debut, date_fin=f_fin)
        except Exception as err:
            st.error(f"Erreur lors du filtrage : {err}")

    if donnees_affichables:
        lignes = []
        for d in donnees_affichables:
            jour_val = d.get("jour") or str(d.get("date", ""))
            nb = d.get("nombre_trajets") or d.get("nb_trajets") or d.get("total_trajets") or 0
            duree = d.get("duree_moyenne_secondes") or 0.0
            duree_min = round(float(duree) / 60.0, 1) if duree else 0.0
            lignes.append({
                "Date": jour_val,
                "Nombre de trajets": int(nb),
                "Duree moyenne (sec)": round(float(duree), 1),
                "Duree moyenne (min)": duree_min,
            })
        df_act = pd.DataFrame(lignes)
        st.dataframe(df_act, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun trajet enregistre pour la periode selectionnee.")

# Onglet 2 : Stations les plus actives
with tab2:
    st.subheader("Classement des 10 stations les plus actives")
    if stations_data:
        lignes_st = []
        for s in stations_data:
            lignes_st.append({
                "Identifiant": s.get("station_id"),
                "Nom de la station": s.get("nom"),
                "Commune": s.get("commune"),
                "Departs": s.get("nb_departs", 0),
                "Arrivees": s.get("nb_arrivees", 0),
                "Total trajets": s.get("total_trajets", 0),
            })
        df_st = pd.DataFrame(lignes_st)
        st.dataframe(df_st, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune donnee de station disponible.")

# Onglet 3 : Incidents par statut
with tab3:
    st.subheader("Repartition des incidents et delai moyen de resolution")
    if incidents_data:
        lignes_inc = []
        for inc in incidents_data:
            delai = inc.get("delai_moyen_heures")
            delai_str = f"{float(delai):.1f} h" if delai is not None else "En cours / Non resolu"
            lignes_inc.append({
                "Statut": str(inc.get("statut", "")).capitalize(),
                "Nombre d'incidents": inc.get("nb_incidents", 0),
                "Delai moyen de resolution": delai_str,
            })
        df_inc = pd.DataFrame(lignes_inc)
        st.dataframe(df_inc, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun incident recense dans la base.")
