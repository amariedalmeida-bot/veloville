"""Page d'accueil et d'authentification VéloVille."""

import streamlit as st
try:
    from front.api_client import client_api
except ModuleNotFoundError:
    from api_client import client_api

st.set_page_config(
    page_title="VéloVille - Connexion",
    page_icon="🚲",
    layout="wide",
)

st.title("VéloVille")
st.write("Portail de consultation des données du service et de son activité.")

# Initialisation de l'état de session
if "token" not in st.session_state:
    st.session_state["token"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

# Si déjà connecté
if st.session_state["token"]:
    st.success(
        f"Session ouverte. Profil actif : **{st.session_state['role'].capitalize()}**."
    )
    if st.button("Se déconnecter"):
        st.session_state["token"] = None
        st.session_state["role"] = None
        st.session_state["username"] = None
        st.rerun()
else:
    st.subheader("Authentification")
    st.write("Veuillez saisir vos identifiants pour accéder aux données du réseau.")

    with st.form("form_login"):
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        soumettre = st.form_submit_button("Se connecter")

    if soumettre:
        if not username or not password:
            st.error("Veuillez renseigner un identifiant et un mot de passe.")
        else:
            token, role, erreur = client_api.login(username, password)
            if token:
                st.session_state["token"] = token
                st.session_state["role"] = role
                st.session_state["username"] = username
                st.success("Connexion réussie !")
                st.rerun()
            else:
                st.error(f"Échec de l'authentification : {erreur}")