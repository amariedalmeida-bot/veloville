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
    ["Tous", "ouvert", "en_cours", "resolu"],
)
filtre_statut = None if statut_choisi == "Tous" else statut_choisi

taille_page = st.selectbox(
    "Incidents par page",
    options=[10, 20, 50],
    index=1,
    key="incidents_taille_page",
)
criteres = (filtre_statut, taille_page)
if st.session_state.get("_incidents_criteres") != criteres:
    st.session_state["_incidents_criteres"] = criteres
    st.session_state["incidents_page"] = 1
else:
    st.session_state.setdefault("incidents_page", 1)

try:
    reponse = client_api.get_incidents(
        token=token,
        page=st.session_state["incidents_page"],
        taille_page=taille_page,
        statut=filtre_statut,
    )
    incidents = reponse.get("resultats", [])
    total = reponse.get("total", 0)
    nombre_pages = max(1, (total + taille_page - 1) // taille_page)

    if st.session_state["incidents_page"] > nombre_pages:
        st.session_state["incidents_page"] = nombre_pages
        st.rerun()

    st.write(f"**Total incidents trouvés :** {total}")

    col_precedente, col_indication, col_suivante = st.columns([1, 2, 1])
    with col_precedente:
        if st.button(
            "Page précédente",
            disabled=st.session_state["incidents_page"] <= 1,
            key="incidents_page_precedente",
        ):
            st.session_state["incidents_page"] -= 1
            st.rerun()
    with col_indication:
        st.write(f"Page {st.session_state['incidents_page']} sur {nombre_pages}")
    with col_suivante:
        if st.button(
            "Page suivante",
            disabled=st.session_state["incidents_page"] >= nombre_pages,
            key="incidents_page_suivante",
        ):
            st.session_state["incidents_page"] += 1
            st.rerun()

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
                    ["ouvert", "en_cours", "resolu"],
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
