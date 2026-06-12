import streamlit as st
import requests
import time
from datetime import datetime

# Streamlit zwingen, den Platz komplett zu nutzen
st.set_page_config(page_title="Fahrer-App", layout="centered", initial_sidebar_state="collapsed")

# --- CSS für ein extrem kompaktes Design ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; padding-left: 0.5rem; padding-right: 0.5rem; }
    .stats-bar { display: flex; justify-content: space-around; background: #222; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; font-size: 14px;}
    .stop-card { background: white; padding: 8px 10px; margin-bottom: 6px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); display: flex; justify-content: space-between; align-items: center; }
    .stop-info { line-height: 1.2; }
    .stop-address { font-weight: bold; font-size: 14px; margin-bottom: 4px; color: #000; }
    .stop-times { font-size: 12px; color: #555; }
    .stop-status { font-weight: 900; font-size: 13px; text-align: right; min-width: 90px; }
    .live-indicator { font-size: 10px; color: #888; text-align: center; margin-bottom: 5px; }
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
    # Live-Indikator
    st.markdown(f'<div class="live-indicator">● {t["Geliefert"]} - {datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)
    
    heute = datetime.now().strftime('%Y-%m-%d')
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/13292/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for route in data.get("routes", []):
                gesamt = route.get("numTotalOrders", 0)
                erledigt = route.get("numDeliveredOrders", 0)
                st.markdown(f'<div class="stats-bar"><div>{t["Stopps"]}: {gesamt}</div><div>{t["Geliefert"]}: {erledigt}</div></div>', unsafe_allow_html=True)
                
                html_list = ""
                for cp in route.get("checkpoints", []):
                    an_str = cp.get('realArrivalTime')
                    start_str = cp.get('deliverSince')
                    ende_str = cp.get('deliverTill')
                    
                    status_text = t["Offen"]
                    color = "gray"
                    ist_time = "--:--"
                    
                    if an_str and start_str and ende_str:
                        ist_time = an_str[11:16]
                        an = datetime.fromisoformat(an_str.replace("Z", "+00:00"))
                        start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                        ende = datetime.fromisoformat(ende_str.replace("Z", "+00:00"))
                        
                        if an < start:
                            diff = int((start - an).total_seconds() / 60)
                            status_text = f"{diff} {t['Früh']}"
                            color = "#0056b3"
                        elif an > ende:
                            diff = int((an - ende).total_seconds() / 60)
                            status_text = f"{diff} {t['Spät']}"
                            color = "#dc3545"
                        else:
                            status_text = t["Pünktlich"]
                            color = "#28a745"
                    
                    html_list += f"""
                    <div class="stop-card" style="border-left: 5px solid {color};">
                        <div class="stop-info">
                            <div class="stop-address">{cp.get('address')}</div>
                            <div class="stop-times">{t['Fenster']}: {start_str[11:16]}-{ende_str[11:16]} | {t['Ist']}: <b>{ist_time}</b></div>
                        </div>
                        <div class="stop-status" style="color: {color};">{status_text}</div>
                    </div>
                    """
                st.markdown(html_list, unsafe_allow_html=True)
        
        # Automatische Aktualisierung alle 60 Sekunden
        time.sleep(60)
        st.rerun()
            
    except Exception as e:
        st.error("Fehler...")
        time.sleep(60)
        st.rerun()
