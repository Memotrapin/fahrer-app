import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Fahrer-Portal", layout="wide")

# Übersetzungen
TRANSLATIONS = {
    "Deutsch": {"Stat": "Stopps", "Gel": "Geliefert", "Zeit": "Zeitfenster", "Plan": "Plan", "An": "Ankunft", "Früh": "min zu früh", "Pünktlich": "Pünktlich", "Spät": "min zu spät", "Offen": "Offen"},
    "English": {"Stat": "Stops", "Gel": "Delivered", "Zeit": "Time", "Plan": "Plan", "An": "Arrival", "Früh": "min early", "Pünktlich": "On time", "Spät": "min late", "Offen": "Open"},
    # ... (weitere Sprachen ergänzen)
}

# Sprachwahl
lang = st.sidebar.selectbox("Sprache", list(TRANSLATIONS.keys()))
t = TRANSLATIONS[lang]

# Login & Dashboard
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    # ... (Login bleibt) ...
    pass 
else:
    heute = "2026-06-09"
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/13292/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    data = requests.get(url).json()
    for route in data.get("routes", []):
        # Oben die Statistik
        col1, col2 = st.columns(2)
        col1.metric("Stopps gesamt", route.get("numTotalOrders", 0))
        col2.metric("Erledigt", route.get("numDeliveredOrders", 0))
        st.write("---")
        
        for cp in route.get("checkpoints", []):
            an_str = cp.get('realArrivalTime')
            plan_str = cp.get('plannedArrivalTime')
            
            status_text = t["Offen"]
            color = "gray"
            
            if an_str and plan_str:
                an = datetime.fromisoformat(an_str.replace("Z", ""))
                plan = datetime.fromisoformat(plan_str.replace("Z", ""))
                diff = int((plan - an).total_seconds() / 60)
                
                if diff > 0: # Zu früh
                    status_text = f"{diff} {t['Früh']}"
                    color = "blue"
                elif diff < -2: # Zu spät (Toleranz 2 Min)
                    status_text = f"{abs(diff)} {t['Spät']}"
                    color = "red"
                else:
                    status_text = t["Pünktlich"]
                    color = "green"

            st.markdown(f"**{cp.get('address')}**")
            st.caption(f"{t['Zeit']}: {cp.get('deliverSince')[11:16]}-{cp.get('deliverTill')[11:16]} | {t['Plan']}: {plan_str[11:16]}")
            st.markdown(f"Status: <b style='color:{color}'>{status_text}</b>", unsafe_allow_html=True)
            st.write("---")
