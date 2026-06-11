import streamlit as st
import requests
from datetime import datetime

# Seiten-Layout
st.set_page_config(page_title="Fahrer-Portal", layout="wide")

# Fahrer-Logins
FAHRER_LOGINS = {"13292": "passwort123"}

# Session-Status initialisieren
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.driver_id = ""

# --- LOGIN BEREICH ---
if not st.session_state.logged_in:
    st.title("🚛 Fahrer-Login")
    uid = st.text_input("Fahrer-ID")
    pwd = st.text_input("Passwort", type="password")
    if st.button("Anmelden"):
        if uid in FAHRER_LOGINS and FAHRER_LOGINS[uid] == pwd:
            st.session_state.driver_id = uid
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Falsche ID oder Passwort.")
else:
    # --- DASHBOARD BEREICH ---
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.title(f"Hallo Fahrer {st.session_state.driver_id}!")
    
    # Datum für Abfrage (heute)
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
                with st.expander(f"📍 Tour {route.get('id')}", expanded=True):
                    # KPIs in Spalten
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Gesamt", route.get("numTotalOrders", 0))
                    c2.metric("Geliefert", route.get("numDeliveredOrders", 0))
                    c3.metric("Verspätet", route.get("numDelayedOrdersPlan", 0))
                    
                    st.write("---")
                    
                    # Checkpoints
                    for cp in route.get("checkpoints", []):
                        an = cp.get('realArrivalTime', '')
                        start = cp.get('deliverSince', '')
                        ende = cp.get('deliverTill', '')
                        
                        status = "✅"
                        if an and start and ende:
                            if an > ende: status = "⚠️"
                        
                        st.write(f"{status} **{cp.get('address')}**")
                        st.caption(f"Zeitfenster: {start[11:16]}-{ende[11:16]} | Ankunft: {an[11:16] if an else '-'}")
        else:
            st.warning("Keine Tour-Daten gefunden.")
    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {e}")
