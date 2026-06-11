import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Fahrer-Portal", layout="centered")

# --- LOGIN ---
FAHRER_LOGINS = {"13292": "passwort123"}
if "logged_in" not in st.session_state: 
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚛 Login")
    uid = st.text_input("Fahrer-ID")
    pwd = st.text_input("Passwort", type="password")
    if st.button("Anmelden"):
        if uid in FAHRER_LOGINS and FAHRER_LOGINS[uid] == pwd:
            st.session_state.logged_in = True
            st.session_state.driver_id = uid
            st.rerun()
else:
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
    
    # Datum für Abfrage
    heute = "2026-06-09" # Zum Testen festes Datum
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        data = requests.get(url).json()
        for route in data.get("routes", []):
            st.subheader(f"📍 Tour {route.get('id')}")
            
            for cp in route.get("checkpoints", []):
                # Daten holen
                an = cp.get('realArrivalTime', '')
                start = cp.get('deliverSince', '')[11:16]
                ende = cp.get('deliverTill', '')[11:16]
                
                # Status-Logik
                status_icon = "✅"
                if not an: status_icon = "⏳"
                elif an > cp.get('deliverTill', ''): status_icon = "⚠️"
                
                # Kompakte Zeile
                with st.container():
                    col1, col2 = st.columns([0.1, 0.9])
                    col1.write(status_icon)
                    col2.markdown(f"**{cp.get('address')}** \n"
                                  f"<small>{start}-{ende} Uhr | An: {an[11:16] if an else 'offen'}</small>", 
                                  unsafe_allow_html=True)
                    st.divider() # Trennlinie für jede Zeile
    except Exception as e:
        st.error("Daten konnten nicht geladen werden.")
