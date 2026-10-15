"""Écran Incidents.

À compléter : tableau filtrable par statut ; pour le rôle exploitant, changement de
statut d'un incident via l'API.
"""
"""Écran Incidents.

Consultation des incidents et modification de statut pour l'exploitant.
"""

import pandas as pd
import streamlit as st

try:
    from front.api_client import ErreurApi, client_api
except ModuleNotFoundError:
    from api_client import ErreurApi, client_api

st.set_page_config(page_title="VéloVille - Incidents", page_icon="⚠️", layout="wide")
st.title("⚠️ Supervision des incidents")

token = st.session_state.get("token")
role = st.session_state.get("role")

if not token:
    st.warning("⚠️ Veuillez vous connecter sur la page d'accueil pour accéder aux incidents.")
    st.stop()

# Filtre par statut
statut_choisi = st.selectbox(
    "Filtrer par statut",
    ["Tous", "OUVERT", "EN_COURS", "RESOLU", "CLOTURE"],
)
filtre_statut = None if statut_choisi == "Tous" else statut_choisi

try:
    reponse = client_api.get_incidents(
        token=token,
        page=1,
        taille_page=100,
        statut=filtre_statut,
    )
    incidents = reponse.get("items", [])
    total = reponse.get("total", 0)

    st.write(f"**Total incidents trouvés :** {total}")

    if incidents:
        df = pd.DataFrame(incidents)
        st.dataframe(df, use_container_width=True)

        # Formulaire de mise à jour pour l'exploitant
        if role == "exploitant":
            st.markdown("---")
            st.subheader("Mettre à jour le statut d'un incident")
            with st.form("form_modif_incident"):
                incident_ids = [inc["incident_id"] for inc in incidents]
                sel_id = st.selectbox("Sélectionner l'incident", incident_ids)
                nouveau_statut = st.selectbox(
                    "Nouveau statut",
                    ["OUVERT", "EN_COURS", "RESOLU", "CLOTURE"],
                )
                valider = st.form_submit_button("Enregistrer la modification")

            if valider:
                try:
                    client_api.modifier_statut_incident(token, sel_id, nouveau_statut)
                    st.success(f"Incident {sel_id} mis à jour avec le statut {nouveau_statut} !")
                    st.rerun()
                except ErreurApi as err:
                    st.error(f"Erreur lors de la mise à jour : {err}")
    else:
        st.info("Aucun incident ne correspond aux filtres.")

except ErreurApi as e:
    st.error(f"Erreur lors de la récupération des incidents : {e}")