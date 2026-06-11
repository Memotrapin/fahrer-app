import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Fahrer-Portal", layout="wide")

# Fahrer-Logins
FAHRER_LOGINS = {"13292": "passwort123"}

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
    
    org_id = "b993a325-6d34-4af5-a955-3d0b5e07cd47"
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId={org_id}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            routes = data.get("routes", [])
            if not routes:
                st.info("Keine Daten für heute gefunden.")
            
            for route in routes:
                st.subheader(f"Tour {route.get('id')}")
                # HIER ZEIGEN WIR DIE DETAILS AN:
                checkpoints = route.get("checkpoints", [])
                if checkpoints:
                    for cp in checkpoints:
                        # Status-Logik
                        start = cp.get('deliverSince', '00:00:00')
                        ende = cp.get('deliverTill', '23:59:59')
                        an = cp.get('realArrivalTime')
                        
                        status = "✅ Pünktlich"
                        if an:
                            if an < start: status = "🚀 Zu früh"
                            elif an > ende: status = "⚠️ Zu spät"
                        
                        st.write(f"📍 **{cp.get('address')}**")
                        st.caption(f"Zeitfenster: {start[11:16]} - {ende[11:16]} | Ankunft: {an[11:16] if an else 'Offen'} | Status: {status}")
                else:
                    st.write("Keine Stopps in dieser Tour gefunden.")
        else:
            st.error(f"Server-Fehler: {response.status_code}")
    except Exception as e:
        st.error(f"Fehler: {e}")
