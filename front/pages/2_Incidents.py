# """Écran Incidents.

# À compléter : tableau filtrable par statut ; pour le rôle exploitant, changement de
# statut d'un incident via l'API.
# """
# """Écran Indicateurs.

# À compléter : trois st.metric et trois tableaux issus des trois endpoints
# /indicateurs. Aucun graphique.
# """
import streamlit as st
import pandas as pd
from api_client import get_incidents, update_statut_incident, ErreurApi

st.set_page_config(page_title="VéloVille - Incidents", page_icon="⚠️", layout="wide")

st.title("⚠️ Suivi et gestion des incidents")

# Vérification de l'authentification
token = st.session_state.get("token")
role = st.session_state.get("role")

if not token:
    st.warning("Veuillez vous connecter depuis la page d'accueil pour accéder aux incidents.")
    st.stop()

# Filtres et pagination
col_filtre, col_page, col_taille = st.columns([2, 1, 1])

with col_filtre:
    statuts_options = ["Tous", "ouvert", "en_cours", "resolu", "clos"]
    choix_statut = st.selectbox("Filtrer par statut :", options=statuts_options)
    statut_filtre = None if choix_statut == "Tous" else choix_statut

with col_page:
    page = st.number_input("Page", min_value=1, value=1, step=1)

with col_taille:
    taille_page = st.selectbox("Nombre par page", options=[10, 20, 50, 100], index=1)

# Chargement des données
try:
    reponse = get_incidents(token=token, statut=statut_filtre, page=page, taille_page=taille_page)
    incidents = reponse.get("incidents", [])
    total = reponse.get("total", len(incidents))
except ErreurApi as e:
    st.error(f"Erreur lors de la récupération des incidents : {e}")
    st.stop()

if not incidents:
    st.info("Aucun incident trouvé.")
else:
    df = pd.DataFrame(incidents)
    st.caption(f"Affichage de {len(df)} incident(s) sur {total} au total.")
    st.dataframe(df, use_container_width=True, hide_index=True)

# Section réservée au rôle exploitant : Modification de statut
if role == "exploitant":
    st.divider()
    st.subheader("🛠️ Mise à jour d'un incident (Rôle Exploitant)")

    with st.form("form_update_incident"):
        c1, c2, c3 = st.columns(3)
        with c1:
            incident_id = st.text_input("Identifiant de l'incident (ex: INC-001)")
        with c2:
            nouveau_statut = st.selectbox("Nouveau statut", ["ouvert", "en_cours", "resolu", "clos"])
        with c3:
            technicien = st.text_input("Technicien (optionnel)", value=st.session_state.get("username", ""))

        soumis = st.form_submit_button("Mettre à jour le statut", type="primary")

        if soumis:
            if not incident_id.strip():
                st.warning("Veuillez renseigner un identifiant d'incident.")
            else:
                try:
                    update_statut_incident(
                        token=token,
                        incident_id=incident_id.strip(),
                        nouveau_statut=nouveau_statut,
                        technicien=technicien.strip() if technicien.strip() else None,
                    )
                    st.success(f"Statut de l'incident {incident_id} mis à jour avec succès !")
                    st.rerun()
                except ErreurApi as e:
                    st.error(f"Échec de la mise à jour : {e}")