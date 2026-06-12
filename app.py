import streamlit as st
import requests
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Fahrer-App", layout="centered", initial_sidebar_state="collapsed")

# CSS für kompaktes Design
st.markdown("""
    <style>
    .stats-bar { display: flex; justify-content: space-around; background: #222; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; font-size: 14px;}
    .stop-card { background: white; padding: 10px; margin-bottom: 6px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); display: flex; justify-content: space-between; align-items: center; }
    .stop-address { font-weight: bold; font-size: 14px; }
    .stop-times { font-size: 12px; color: #555; }
    .stop-status { font-weight: 900; font-size: 13px; text-align: right; }
    </style>
""", unsafe_allow_html=True)

# Sprachen...
TRANSLATIONS = {
    "Deutsch": {"Stopps": "Stopps", "Geliefert": "Geliefert", "Fenster": "Fenster", "Plan": "Plan", "Ist": "Ist", "Früh": "min zu früh", "Pünktlich": "Pünktlich", "Spät": "min zu spät", "Offen": "Offen"},
    "English": {"Stopps": "Stops", "Geliefert": "Delivered", "Fenster": "Window", "Plan": "Plan", "Ist": "Actual", "Früh": "min early", "Pünktlich": "On time", "Spät": "min late", "Offen": "Open"},
    # ... (restliche Sprachen)
}

# Hilfsfunktion für Zeit + 2h
def fix_time(time_str):
    if not time_str: return None
    # Entferne 'Z' oder '+00:00' und wandle um
    clean_str = time_str.replace("Z", "").split("+")[0]
    dt = datetime.fromisoformat(clean_str)
    return dt + timedelta(hours=2)

# App-Logik
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    # ... (Login bleibt) ...
    uid = st.text_input("Fahrer-ID")
    pwd = st.text_input("Passwort", type="password")
    if st.button("Anmelden"):
        if uid == "13292" and pwd == "passwort123":
            st.session_state.logged_in = True
            st.rerun()
else:
    heute = datetime.now().strftime('%Y-%m-%d')
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/13292/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        data = requests.get(url).json()
        for route in data.get("routes", []):
            st.markdown(f'<div class="stats-bar"><div>Stopps: {route.get("numTotalOrders")}</div><div>Geliefert: {route.get("numDeliveredOrders")}</div></div>', unsafe_allow_html=True)
            
            for cp in route.get("checkpoints", []):
                # Zeit korrigieren
                an = fix_time(cp.get('realArrivalTime'))
                start = fix_time(cp.get('deliverSince'))
                ende = fix_time(cp.get('deliverTill'))
                
                status_text = "Offen"; color = "gray"
                
                if an and start and ende:
                    if an < start:
                        diff = int((start - an).total_seconds() / 60)
                        status_text = f"{diff} min früh"; color = "blue"
                    elif an > ende:
                        diff = int((an - ende).total_seconds() / 60)
                        status_text = f"{diff} min spät"; color = "red"
                    else:
                        status_text = "Pünktlich"; color = "green"
                
                st.markdown(f"""
                <div class="stop-card" style="border-left: 5px solid {color};">
                    <div class="stop-info">
                        <div class="stop-address">{cp.get('address')}</div>
                        <div class="stop-times">Zeit: {start.strftime("%H:%M")}-{ende.strftime("%H:%M")} | Ist: <b>{an.strftime("%H:%M") if an else '--:--'}</b></div>
                    </div>
                    <div class="stop-status" style="color: {color};">{status_text}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Automatischer Refresh
        time.sleep(60)
        st.rerun()
    except Exception as e:
        st.error(f"Fehler: {e}")
