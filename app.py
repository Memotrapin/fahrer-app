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
            st.error("Falsche ID oder Passwort.")
else:
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.title(f"Tour-Details für heute")
    
    heute = datetime.now().strftime('%Y-%m-%d')
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            routes = response.json().get("routes", [])
            for route in routes:
                with st.expander(f"📍 Tour {route.get('id')}", expanded=True):
                    # KPIs
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Pakete", route.get("numTotalOrders", 0))
                    c2.metric("Geliefert", route.get("numDeliveredOrders", 0))
                    c3.metric("Verspätungen", route.get("numDelayedOrdersPlan", 0))
                    
                    st.write("---")
                    
                    for cp in route.get("checkpoints", []):
                        # Zeiten abrufen
                        plan = cp.get('plannedArrivalTime', '')
                        real = cp.get('realArrivalTime', '')
                        start = cp.get('deliverSince', '')
                        ende = cp.get('deliverTill', '')
                        
                        # Zeit-Formatierung (HH:MM)
                        p_zeit = plan[11:16] if plan else "-"
                        r_zeit = real[11:16] if real else "-"
                        
                        # Logik: Früh/Spät/Pünktlich
                        if not real:
                            status = "⏳ Offen"
                            color = "gray"
                        elif real < start:
                            status = "🚀 Zu früh"
                            color = "blue"
                        elif real > ende:
                            status = "⚠️ Zu spät"
                            color = "red"
                        else:
                            status = "✅ Pünktlich"
                            color = "green"
                            
                        st.markdown(f"**{cp.get('position')}. {cp.get('address')}**")
                        st.write(f"Zeitfenster: {start[11:16]}-{ende[11:16]} | Geplant: {p_zeit} | Ist: {r_zeit}")
                        st.markdown(f"Status: :{color}[{status}]")
                        st.write("---")
        else:
            st.warning("Keine Tour-Daten für heute verfügbar.")
    except Exception as e:
        st.error(f"Fehler: {e}")
