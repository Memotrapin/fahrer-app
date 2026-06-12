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
            
            # --- 2. KOMPAKTE STOPP-LISTE (ALLES IN HTML) ---
            html_list = ""
            for cp in route.get("checkpoints", []):
                an_str = cp.get('realArrivalTime')
                plan_str = cp.get('plannedArrivalTime')
                start_str = cp.get('deliverSince', 'T00:00')
                ende_str = cp.get('deliverTill', 'T00:00')
                
                status_text = t["Offen"]
                color = "gray"
                ist_time = "--:--"
                
                # Zeit-Differenz berechnen (Plan vs. Ist)
                if an_str and plan_str:
                    ist_time = an_str[11:16]
                    try:
                        an = datetime.fromisoformat(an_str.replace("Z", "+00:00"))
                        plan = datetime.fromisoformat(plan_str.replace("Z", "+00:00"))
                        diff = int((plan - an).total_seconds() / 60)
                        
                        if diff > 0: # Zu früh
                            status_text = f"{diff} {t['Früh']}"
                            color = "#0056b3" # Blau
                        elif diff < 0: # Zu spät
                            status_text = f"{abs(diff)} {t['Spät']}"
                            color = "#dc3545" # Rot
                        else:
                            status_text = t["Pünktlich"]
                            color = "#28a745" # Grün
                    except:
                        pass
                
                # Jeder Stopp ist eine eng gepackte Zeile
                html_list += f"""
                <div class="stop-card" style="border-left: 5px solid {color};">
                    <div class="stop-info">
                        <div class="stop-address">{cp.get('address')}</div>
                        <div class="stop-times">
                            {t['Fenster']}: {start_str[11:16]}-{ende_str[11:16]} &nbsp;|&nbsp; 
                            {t['Plan']}: {plan_str[11:16] if plan_str else '--'} &nbsp;|&nbsp; 
                            {t['Ist']}: <b>{ist_time}</b>
                        </div>
                    </div>
                    <div class="stop-status" style="color: {color};">
                        {status_text}
                    </div>
                </div>
                """
            
            # Die komplette Liste als einen einzigen kompakten Block ausgeben
            st.markdown(html_list, unsafe_allow_html=True)
            
    except Exception as e:
        st.error("Fehler beim Laden der Daten.")
