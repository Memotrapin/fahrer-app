import streamlit as st
import requests
from datetime import datetime, timedelta

# --- KONFIGURATION ---
# Deine Supabase-Daten
SUPABASE_URL = "https://eytdvmenynabwltnryto.supabase.co"
# TRAGE HIER DEINEN ECHTEN KEY EIN:
SUPABASE_KEY = "sb_publishable_2ylpUDTGGt9CfCW-75nwDg_j6ChUpgP" 

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
        url = f"{SUPABASE_URL}/rest/v1/drivers?id=eq.{uid}&passwort=eq.{pwd}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        
        try:
            response = requests.get(url, headers=headers).json()
            
            if response:
                user_data = response[0]
                st.session_state.logged_in = True
                st.session_state.driver_id = str(uid)
                st.session_state.driver_name = user_data.get('name', 'Fahrer')
                st.rerun()
            else:
                st.error("ID oder Passwort falsch.")
        except Exception as e:
            st.error("Fehler bei der Verbindung zur Datenbank.")
            
# --- FAHRER-DASHBOARD ---
else:
    # Ausloggen-Button in der ausklappbaren Sidebar links platzieren
    with st.sidebar:
        if st.button("🚪 Ausloggen"):
            st.session_state.logged_in = False
            st.session_state.driver_id = ""
            st.session_state.driver_name = ""
            st.rerun()
            
    # Begrüßung des Fahrers ganz oben
    st.subheader(f"Hallo {st.session_state.driver_name} 👋")
    
    # Sprachauswahl unter der Begrüßung
    lang = st.selectbox("Sprache / Language", list(TRANSLATIONS.keys()))
    t = TRANSLATIONS[lang]
    
    # Heutiges Datum holen und Touren-API abfragen
    heute = datetime.now().strftime('%Y-%m-%d')
    tour_url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        response = requests.get(tour_url)
        if response.status_code == 200:
            data = response.json()
            routes = data.get("routes", [])
            
            # WICHTIG: Wenn die Liste leer ist, zeigen wir das an!
            if not routes:
                st.info("Keine Touren für heute geplant.")
                
            for route in routes:
                # Statistik-Balken oben
                st.markdown(f'<div class="stats-bar"><div>{t["Stopps"]}: {route.get("numTotalOrders")}</div><div>{t["Geliefert"]}: {route.get("numDeliveredOrders")}</div></div>', unsafe_allow_html=True)
                
                html_list = ""
                for cp in route.get("checkpoints", []):
                    an = fix_time(cp.get('realArrivalTime'))
                    start = fix_time(cp.get('deliverSince'))
                    ende = fix_time(cp.get('deliverTill'))
                    
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
                    
                    # Einzelne Adresskarte zusammenbauen
                    html_list += f"""
                    <div class="stop-card" style="border-left: 5px solid {color};">
                        <div class="stop-address">{cp.get('address')}</div>
                        <div class="stop-times">{t['Fenster']}: {start.strftime("%H:%M") if start else '--'}-{ende.strftime("%H:%M") if ende else '--'} | {t['Ist']}: <b>{an.strftime("%H:%M") if an else '--'}</b></div>
                        <div class="stop-status" style="color: {color};">{status_text}</div>
                    </div>
                    """
                st.markdown(html_list, unsafe_allow_html=True)
                
            # Manueller Aktualisieren-Button
            st.write("---")
            if st.button("🔄 Daten aktualisieren"):
                st.rerun()
                
        else:
            st.error(f"Tourdaten konnten nicht geladen werden. Fehlercode: {response.status_code}")
            
    except Exception as e:
        st.error(f"Fehler bei der Verbindung zum Server: {e}")
