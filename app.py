import streamlit as st
import requests
import time
from datetime import datetime, timedelta

# --- KONFIGURATION (HIER DEINE DATEN EINTRAGEN) ---
SUPABASE_URL = "https://eytdvmenynabwltnryto.supabase.co"
SUPABASE_KEY = "DEIN_ANON_KEY_HIER" # Den Publishable Key aus dem API-Tab

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

# Übersetzungen
TRANSLATIONS = {
    "Deutsch": {"Stopps": "Stopps", "Geliefert": "Geliefert", "Fenster": "Fenster", "Plan": "Plan", "Ist": "Ist", "Früh": "min früh", "Pünktlich": "Pünktlich", "Spät": "min spät", "Offen": "Offen"},
    "English": {"Stopps": "Stops", "Geliefert": "Delivered", "Fenster": "Window", "Plan": "Plan", "Ist": "Actual", "Früh": "min early", "Pünktlich": "On time", "Spät": "min late", "Offen": "Open"},
    "Türkçe": {"Stopps": "Duraklar", "Geliefert": "Teslim", "Fenster": "Pencere", "Plan": "Plan", "Ist": "Gelen", "Früh": "dk erken", "Pünktlich": "Zamanında", "Spät": "dk geç", "Offen": "Açık"},
    "Русский": {"Stopps": "Остановки", "Geliefert": "Доставлено", "Fenster": "Окно", "Plan": "План", "Ist": "Факт", "Früh": "мин рано", "Pünktlich": "Вовремя", "Spät": "мин поздно", "Offen": "Открыто"},
    "العربية": {"Stopps": "توقف", "Geliefert": "تم التوصيل", "Fenster": "نافذة", "Plan": "خطة", "Ist": "فعلي", "Früh": "دقيقة مبكر", "Pünktlich": "في الموعد", "Spät": "دقيقة متأخر", "Offen": "مفتوح"}
}

def fix_time(time_str):
    if not time_str: return None
    clean_str = time_str.replace("Z", "").split("+")[0]
    return datetime.fromisoformat(clean_str) + timedelta(hours=2)

# Login-Zustand
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚛 Fahrer-Login")
    uid = st.text_input("Fahrer-ID")
    pwd = st.text_input("Passwort", type="password")
    if st.button("Anmelden"):
        # Login gegen Supabase
        url = f"{SUPABASE_URL}/rest/v1/drivers?id=eq.{uid}&passwort=eq.{pwd}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(url, headers=headers).json()
        
        if response:
            st.session_state.logged_in = True
            st.session_state.driver_id = uid
            st.session_state.driver_name = response[0]['name']
            st.rerun()
        else:
            st.error("ID oder Passwort falsch.")
else:
    # Sidebar für Logout
    with st.sidebar:
        if st.button("🚪 Ausloggen"):
            st.session_state.logged_in = False
            st.rerun()
    
    st.subheader(f"Hallo {st.session_state.driver_name} 👋")
    lang = st.sidebar.selectbox("Sprache", list(TRANSLATIONS.keys()))
    t = TRANSLATIONS[lang]
    
    heute = datetime.now().strftime('%Y-%m-%d')
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for route in data.get("routes", []):
                st.markdown(f'<div class="stats-bar"><div>{t["Stopps"]}: {route.get("numTotalOrders")}</div><div>{t["Geliefert"]}: {route.get("numDeliveredOrders")}</div></div>', unsafe_allow_html=True)
                
                html_list = ""
                for cp in route.get("checkpoints", []):
                    an = fix_time(cp.get('realArrivalTime'))
                    start = fix_time(cp.get('deliverSince'))
                    ende = fix_time(cp.get('deliverTill'))
                    plan = fix_time(cp.get('plannedArrivalTime'))
                    
                    status_text = t["Offen"]; color = "gray"
                    if an and start and ende:
                        if an < start:
                            diff = int((start - an).total_seconds() / 60)
                            status_text = f"{diff} {t['Früh']}"; color = "#0056b3"
                        elif an > ende:
                            diff = int((an - ende).total_seconds() / 60)
                            status_text = f"{diff} {t['Spät']}"; color = "#dc3545"
                        else:
                            status_text = t["Pünktlich"]; color = "#28a745"
                    
                    html_list += f"""
                    <div class="stop-card" style="border-left: 5px solid {color};">
                        <div class="stop-address">{cp.get('address')}</div>
                        <div class="stop-times">{t['Fenster']}: {start.strftime("%H:%M")}-{ende.strftime("%H:%M")} | {t['Ist']}: <b>{an.strftime("%H:%M") if an else '--'}</b></div>
                        <div class="stop-status" style="color: {color};">{status_text}</div>
                    </div>
                    """
                st.markdown(html_list, unsafe_allow_html=True)
        time.sleep(60); st.rerun()
    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")
