# """Page d'accueil Streamlit : connexion.

# À compléter : formulaire identifiant / mot de passe, appel de POST /auth/login via
# api_client, stockage du jeton et du rôle dans st.session_state,
# message d'erreur en français en cas d'échec.

# Lancement : streamlit run front/app.py
# """
# """Page d'accueil Streamlit : connexion.

# # Formulaire identifiant / mot de passe, appel de POST /auth/login via
# api_client, stockage du jeton et du rôle dans st.session_state,
# message d'erreur en français en cas d'échec.

# Lancement : streamlit run front/app.py
# """

import streamlit as st
from api_client import login

st.set_page_config(
    page_title="VéloVille - Connexion",
    page_icon="🚲",
    layout="centered",
)

# Initialisation des variables de session
if "token" not in st.session_state:
    st.session_state["token"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

st.title("🚲 VéloVille - Portail de gestion")

# Affichage selon l'état d'authentification
if st.session_state["token"]:
    st.success(f"Connecté en tant que **{st.session_state['username']}** (Rôle : *{st.session_state['role']}*).")
    st.info("Utilisez le menu de gauche pour naviguer entre les différentes vues (Stations, Incidents, Indicateurs).")

    if st.button("Se déconnecter", type="secondary"):
        st.session_state["token"] = None
        st.session_state["role"] = None
        st.session_state["username"] = None
        st.rerun()

else:
    st.subheader("Authentification")
    st.write("Veuillez vous identifier pour accéder aux services.")

    with st.form("form_connexion"):
        username = st.text_input("Identifiant", placeholder="ex: exploitant1")
        password = st.text_input("Mot de passe", type="password")
        soumis = st.form_submit_button("Se connecter", type="primary")

        if soumis:
            if not username.strip() or not password:
                st.warning("Veuillez renseigner votre identifiant et votre mot de passe.")
            else:
                try:
                    reponse = login(username.strip(), password)
                    # Récupération du jeton et du rôle renvoyés par l'API
                    st.session_state["token"] = reponse.get("access_token")
                    st.session_state["role"] = reponse.get("role")
                    st.session_state["username"] = username.strip()
                    st.success("Connexion réussie !")
                    st.rerun()
                except Exception as e:
                    message_erreur = str(e)
                    if "401" in message_erreur or "Unauthorized" in message_erreur:
                        st.error("Identifiant ou mot de passe incorrect.")
                    else:
                        st.error(f"Erreur lors de la tentative de connexion : {message_erreur}")