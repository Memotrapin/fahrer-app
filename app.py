import streamlit as st
import requests
from datetime import datetime

# Streamlit zwingen, den Platz komplett zu nutzen
st.set_page_config(page_title="Fahrer-App", layout="centered", initial_sidebar_state="collapsed")

# --- CSS: Schmeißt alle ungenutzten Flächen und Abstände raus ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; padding-left: 0.5rem; padding-right: 0.5rem; }
    .stats-bar { display: flex; justify-content: space-around; background: #222; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; font-size: 14px;}
    .stop-card { background: white; padding: 8px 10px; margin-bottom: 6px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); display: flex; justify-content: space-between; align-items: center; }
    .stop-info { line-height: 1.2; }
    .stop-address { font-weight: bold; font-size: 14px; margin-bottom: 4px; color: #000; }
    .stop-times { font-size: 12px; color: #555; }
    .stop-status { font-weight: 900; font-size: 13px; text-align: right; min-width: 90px; }
    </style>
""", unsafe_allow_html=True)

# Sprachen
TRANSLATIONS = {
    "Deutsch": {"Stopps": "Stopps", "Geliefert": "Geliefert", "Fenster": "Fenster", "Plan": "Plan", "Ist": "Ist", "Früh": "min zu früh", "Pünktlich": "Pünktlich", "Spät": "min zu spät", "Offen": "Offen"},
    "English": {"Stopps": "Stops", "Geliefert": "Delivered", "Fenster": "Window", "Plan": "Plan", "Ist": "Actual", "Früh": "min early", "Pünktlich": "On time", "Spät": "min late", "Offen": "Open"},
    "Türkçe": {"Stopps": "Duraklar", "Geliefert": "Teslim", "Fenster": "Pencere", "Plan": "Plan", "Ist": "Gelen", "Früh": "dk erken", "Pünktlich": "Zamanında", "Spät": "dk geç", "Offen": "Açık"},
    "Русский": {"Stopps": "Остановки", "Geliefert": "Доставлено", "Fenster": "Окно", "Plan": "План", "Ist": "Факт", "Früh": "мин рано", "Pünktlich": "Вовремя", "Spät": "мин поздно", "Offen": "Открыто"},
    "العربية": {"Stopps": "توقف", "Geliefert": "تم التوصيل", "Fenster": "نافذة", "Plan": "خطة", "Ist": "فعلي", "Früh": "دقيقة مبكر", "Pünktlich": "في الموعد", "Spät": "دقيقة متأخر", "Offen": "مفتوح"}
}

lang = st.sidebar.selectbox("Sprache / Language", list(TRANSLATIONS.keys()))
t = TRANSLATIONS[lang]

if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚛 Login")
    uid = st.text_input("Fahrer-ID")
    pwd = st.text_input("Passwort", type="password")
    if st.button("Anmelden"):
        if uid == "13292" and pwd == "passwort123":
            st.session_state.logged_in = True
            st.rerun()
else:
    heute = "2026-06-09" # Festes Datum zum Testen
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/13292/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        data = requests.get(url).json()
        for route in data.get("routes", []):
            
            # --- 1. KOMPAKTE STATISTIK GANZ OBEN ---
            gesamt = route.get("numTotalOrders", 0)
            erledigt = route.get("numDeliveredOrders", 0)
            st.markdown(f'<div class="stats-bar"><div>{t["Stopps"]}: {gesamt}</div><div>{t["Geliefert"]}: {erledigt}</div></div>', unsafe_allow_html=True)
            
            # ---
