import streamlit as st
import requests
import time
from datetime import datetime, timedelta

# --- KONFIGURATION ---
# Deine Supabase-Daten (Bleiben für dein Projekt immer gleich)
SUPABASE_URL = "https://eytdvmenynabwltnryto.supabase.co"
SUPABASE_KEY = "sb_publishable_2ylpUDTGGT9CfcW-75nwDg_j6ChU" # Setze hier deinen vollen Publishable Key ein

st.set_page_config(page_title="Fahrer-App", layout="centered", initial_sidebar_state="collapsed")

# --- CSS FÜR HANDY-OPTIMIERUNG ---
st.markdown("""
    <style>
    .block-container { padding: 10px; }
    .stats-bar { display: flex; justify-content: space-around; background: #222; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; font-size: 14px;}
    .stop-card { background: white; padding: 10px; margin-bottom: 8px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); display: flex; flex-direction: column; }
    .stop-address { font-weight: bold; font-size: 15px; color: #000; margin-bottom: 5px; word-wrap: break-word; }
    .stop-times { font-size: 12px; color: #555; margin-bottom: 5px; }
    .stop-status { font-weight: 900; font-size: 13px; align-self: flex-start; }
    </style>
""", unsafe_allow_html=True)

# Übersetzungen für das Dashboard
TRANSLATIONS = {
    "Deutsch": {"Stopps": "Stopps", "Geliefert": "Geliefert", "Fenster": "Fenster", "Plan": "Plan", "Ist": "Ist", "Früh": "min früh", "Pünktlich": "Pünktlich", "Spät": "min spät", "Offen": "Offen"},
    "English": {"Stopps": "Stops", "Geliefert": "Delivered", "Fenster": "Window", "Plan": "Plan", "Ist": "Actual", "Früh": "min early", "Pünktlich": "On time", "Spät": "min late", "Offen": "Open"},
    "Türkçe": {"Stopps": "Duraklar", "Geliefert": "Teslim", "Fenster": "Pencere", "Plan": "Plan", "Ist": "Gelen", "Früh": "dk erken", "Pünktlich": "Zamanında", "Spät": "dk geç", "Offen": "Açık"},
    "Русский": {"Stopps": "Остановки", "Geliefert": "Доставлено", "Fenster": "Окно", "Plan": "План", "Ist": "Факт", "Früh": "мин рано", "Pünktlich": "Вовремя", "Spät": "мин поздно", "Offen": "Открыто"},
    "العربية": {"Stopps": "توقف", "Geliefert": "تم التوصيل", "Fenster": "نافذة", "Plan": "خطة", "Ist": "فعلي", "Früh": "دقيقة مبكر", "Pünktlich": "في الموعد", "Spät": "دقيقة متأخر", "Offen": "مفتوح"}
}

# Hilfsfunktion für die Zeitkorrektur um +2 Stunden
def fix_time(time_str):
    if not time_str: return None
    clean_str = time_str.replace("Z", "").split("+")[0]
    return datetime.fromisoformat(clean_str) + timedelta(hours=2)

# Überprüfen des Login-Status im Session State
if "logged_in" not in st.session_state: 
    st.session_state.logged_in = False

# --- ANMELDE-FENSTER ---
if not st.session_state.logged_in:
    st.title("🚛 Fahrer-Login")
    uid = st.text_input("Fahrer-ID")
    pwd = st.text_input("Passwort", type="password")
    
    if st.button("Anmelden"):
        # Abfrage an deine 'drivers' Tabelle in Supabase
        url = f"{SUPABASE_URL}/rest/v1/drivers?id=eq.{uid}&passwort=eq.{pwd}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        
        try:
            response = requests.get(url, headers=headers).json()
            
            if response: # Wenn ein Eintrag gefunden wurde
                user_data = response[0]
                st.session_state.logged_in = True
                st.session_state.driver_id = str(uid)
                # Holt das Feld 'name' ab. Wenn keines da ist, wird 'Fahrer' als Standard
