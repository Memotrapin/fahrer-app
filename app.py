import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Fahrer-Portal", layout="wide")

# Konfiguration der Zugangsdaten
# Hier kannst du beliebig viele IDs und deren Passwörter hinterlegen
FAHRER_LOGINS = {
    "13292": "passwort123",
    "12345": "geheimnis",
    "10004": "yokya"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.driver_id = ""

if not st.session_state.logged_in:
    st.title("🚛 Fahrer-Login")
    input_id = st.text_input("Fahrer-ID")
    input_pass = st.text_input("Passwort", type="password") # Versteckte Eingabe
    
    if st.button("Anmelden"):
        # Überprüfung: ID vorhanden UND Passwort korrekt?
        if input_id in FAHRER_LOGINS and FAHRER_LOGINS[input_id] == input_pass:
            st.session_state.driver_id = input_id
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Falsche ID oder falsches Passwort.")

else:
    # --- Dashboard ---
    st.sidebar.button("Abmelden", on_click=lambda: st.session_state.update({"logged_in": False}))
    
    # Hier kommt dein restlicher Dashboard-Code von vorhin hin...
    st.write(f"Willkommen, Fahrer {st.session_state.driver_id}")
    # (Restlicher Code zur Datenabfrage...)
