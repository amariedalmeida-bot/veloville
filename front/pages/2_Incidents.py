"""Ã‰cran Incidents.

Ã€ complÃ©ter : tableau filtrable par statut ; pour le rÃ´le exploitant, changement de
statut d'un incident via l'API.
"""
"""Ã‰cran Incidents.

Consultation des incidents et modification de statut pour l'exploitant.
"""

import pandas as pd
import streamlit as st

try:
    from front.api_client import ErreurApi, client_api
except ModuleNotFoundError:
    from api_client import ErreurApi, client_api

st.set_page_config(page_title="VÃ©loVille - Incidents", page_icon="âš ï¸", layout="wide")
st.title("âš ï¸ Supervision des incidents")

token = st.session_state.get("token")
role = st.session_state.get("role")

if not token:
    st.warning("âš ï¸ Veuillez vous connecter sur la page d'accueil pour accÃ©der aux incidents.")
    st.stop()

# Filtre par statut
statut_choisi = st.selectbox(
    "Filtrer par statut",
    ["Tous", "ouvert", "en_cours", "resolu"],
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

    st.write(f"**Total incidents trouvÃ©s :** {total}")

    if incidents:
        df = pd.DataFrame(incidents)
        st.dataframe(df, use_container_width=True)

        # Formulaire de mise Ã  jour pour l'exploitant
        if role == "exploitant":
            st.markdown("---")
            st.subheader("Mettre Ã  jour le statut d'un incident")
            with st.form("form_modif_incident"):
                incident_ids = [inc["incident_id"] for inc in incidents]
                sel_id = st.selectbox("SÃ©lectionner l'incident", incident_ids)
                nouveau_statut = st.selectbox(
                    "Nouveau statut",
                    ["ouvert", "en_cours", "resolu"],
                )
                valider = st.form_submit_button("Enregistrer la modification")

            if valider:
                try:
                    client_api.modifier_statut_incident(token, sel_id, nouveau_statut)
                    st.success(f"Incident {sel_id} mis Ã  jour avec le statut {nouveau_statut} !")
                    st.rerun()
                except ErreurApi as err:
                    st.error(f"Erreur lors de la mise Ã  jour : {err}")
    else:
        st.info("Aucun incident ne correspond aux filtres.")

except ErreurApi as e:
    st.error(f"Erreur lors de la rÃ©cupÃ©ration des incidents : {e}")
