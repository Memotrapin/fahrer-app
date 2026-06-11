import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Fahrer-Portal", layout="wide")

# Fahrer-Logins
FAHRER_LOGINS = {"13292": "passwort123", "12345": "geheimnis"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.driver_id = ""

if not st.session_state.logged_in:
    st.title("🚛 Fahrer-Login")
    input_id = st.text_input("Fahrer-ID")
    input_pass = st.text_input("Passwort", type="password")
    if st.button("Anmelden"):
        if input_id in FAHRER_LOGINS and FAHRER_LOGINS[input_id] == input_pass:
            st.session_state.driver_id = input_id
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Falsche ID oder Passwort.")
else:
    st.sidebar.button("Abmelden", on_click=lambda: st.session_state.update({"logged_in": False}))
    
    st.title(f"Hallo Fahrer {st.session_state.driver_id}!")
    heute = datetime.now().strftime('%Y-%m-%d')
    st.write(f"Datum für Abfrage: {heute}")
    
    org_id = "b993a325-6d34-4af5-a955-3d0b5e07cd47"
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId={org_id}"
    
    # --- HIER IST DER TRY-BLOCK ---
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            routes = data.get("routes", [])
            if not routes:
                st.info("Keine Daten für heute gefunden.")
            for route in routes:
                st.write(f"### Tour {route.get('id')}")
                # ... hier kommen deine Tabellen ...
        else:
            st.warning(f"Keine Daten gefunden (Status: {response.status_code})")
    except Exception as e:
        st.error(f"Fehler bei der Verbindung: {e}")
    # --- ENDE DES TRY-BLOCKS ---
