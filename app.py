import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Fahrer-Portal", layout="wide")

FAHRER_LOGINS = {"13292": "passwort123"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.driver_id = ""

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
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.title(f"Tour-Übersicht")
    
    # TEST: Hier das Datum fest auf den 09.06.2026 setzen, um Daten zu sehen
    heute = "2026-06-09" 
    
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            routes = response.json().get("routes", [])
            for route in routes:
                st.subheader(f"📍 Tour {route.get('id')}")
                
                # Kompakter Header
                c1, c2, c3 = st.columns(3)
                c1.metric("Pakete", route.get("numTotalOrders", 0))
                c2.metric("Geliefert", route.get("numDeliveredOrders", 0))
                c3.metric("Verspätet", route.get("numDelayedOrdersPlan", 0))
                
                st.write("") # Abstand
                
                # KOMPAKTE STOPPS: Nur eine Zeile pro Stopp
                for cp in route.get("checkpoints", []):
                    an = cp.get('realArrivalTime', '')
                    start = cp.get('deliverSince', '')
                    ende = cp.get('deliverTill', '')
                    
                    status_icon = "✅"
                    if an and an > ende: status_icon = "⚠️"
                    elif not an: status_icon = "⏳"
                    
                    # Hier wird der Stopp in einer kompakten Zeile angezeigt
                    with st.expander(f"{status_icon} Stopp {cp.get('position')}: {cp.get('address')}"):
                        st.write(f"**Zeitfenster:** {start[11:16]} - {ende[11:16]}")
                        st.write(f"**Geplant:** {cp.get('plannedArrivalTime', '-')[11:16]}")
                        st.write(f"**Tatsächlich:** {an[11:16] if an else 'Noch offen'}")
        else:
            st.warning("Keine Daten gefunden.")
    except Exception as e:
        st.error(f"Fehler: {e}")
