import streamlit as st
import requests
import time
from datetime import datetime, timedelta

# --- KONFIGURATION ---
SUPABASE_URL = "DEINE_SUPABASE_URL_HIER"
SUPABASE_KEY = "DEIN_ANON_KEY_HIER"

st.set_page_config(page_title="Fahrer-App", layout="centered", initial_sidebar_state="collapsed")

# --- CSS ---
st.markdown("""
    <style>
    .stats-bar { display: flex; justify-content: space-around; background: #222; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; font-size: 14px;}
    .stop-card { background: white; padding: 10px; margin-bottom: 8px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); display: flex; flex-direction: column; }
    .stop-address { font-weight: bold; font-size: 15px; color: #000; margin-bottom: 5px; }
    .stop-times { font-size: 12px; color: #555; margin-bottom: 5px; }
    .stop-status { font-weight: 900; font-size: 13px; align-self: flex-start; }
    </style>
""", unsafe_allow_html=True)

# Hilfsfunktion für Zeit
def fix_time(time_str):
    if not time_str: return None
    clean_str = time_str.replace("Z", "").split("+")[0]
    return datetime.fromisoformat(clean_str) + timedelta(hours=2)

# Login & Datenabfrage
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚛 Fahrer-Login")
    uid = st.text_input("Fahrer-ID")
    pwd = st.text_input("Passwort", type="password")
    
    if st.button("Anmelden"):
        # Supabase Abfrage
        url = f"{SUPABASE_URL}/rest/v1/drivers?id=eq.{uid}&passwort=eq.{pwd}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(url, headers=headers).json()
        
        if response:
            st.session_state.logged_in = True
            st.session_state.driver_id = uid
            st.session_state.driver_name = response[0]['name'] # Name aus DB
            st.rerun()
        else:
            st.error("ID oder Passwort falsch.")
else:
    # Begrüßung
    st.subheader(f"Hallo {st.session_state.driver_name} 👋")
    
    # Sprachwahl & Tour-Daten
    lang = st.sidebar.selectbox("Sprache", ["Deutsch", "English", "Türkçe", "Русский", "العربية"])
    
    heute = datetime.now().strftime('%Y-%m-%d')
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        data = requests.get(url).json()
        for route in data.get("routes", []):
            st.markdown(f'<div class="stats-bar"><div>Stopps: {route.get("numTotalOrders")}</div><div>Geliefert: {route.get("numDeliveredOrders")}</div></div>', unsafe_allow_html=True)
            
            for cp in route.get("checkpoints", []):
                an = fix_time(cp.get('realArrivalTime'))
                start = fix_time(cp.get('deliverSince'))
                ende = fix_time(cp.get('deliverTill'))
                
                # Status Logik... (bleibt gleich)
                status_text = "Offen"; color = "gray"
                if an and start and ende:
                    if an < start: status_text = "früh"; color = "#0056b3"
                    elif an > ende: status_text = "spät"; color = "#dc3545"
                    else: status_text = "Pünktlich"; color = "#28a745"
                
                st.markdown(f"""
                <div class="stop-card" style="border-left: 5px solid {color};">
                    <div class="stop-address">{cp.get('address')}</div>
                    <div class="stop-times">Fenster: {start.strftime("%H:%M")}-{ende.strftime("%H:%M")} | Ist: <b>{an.strftime("%H:%M") if an else '--'}</b></div>
                    <div class="stop-status" style="color: {color};">{status_text}</div>
                </div>
                """, unsafe_allow_html=True)
        time.sleep(60); st.rerun()
    except Exception as e:
        st.error("Fehler beim Laden der Tour.")
