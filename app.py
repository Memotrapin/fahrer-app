import streamlit as st
import requests
import pandas as pd
import concurrent.futures  # NEU: Für gleichzeitiges (paralleles) Laden
from datetime import datetime, timedelta

# --- KONFIGURATION ---
SUPABASE_URL = "https://eytdvmenynabwltnryto.supabase.co"
# TRAGE HIER DEINEN ECHTEN KEY EIN:
SUPABASE_KEY = "sb_publishable_2ylpUDTGGt9CfCW-75nwDg_j6ChUpgP" 

st.set_page_config(page_title="Fahrer & Admin App", layout="wide", initial_sidebar_state="collapsed")

# --- CSS FÜR HANDY & KARTEN ---
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
    "English": {"Stopps": "Stops", "Geliefert": "Delivered", "Fenster": "Window", "Plan": "Plan", "Ist": "Actual", "Früh": "min early", "Pünktlich": "On time", "Spät": "min late", "Offen": "Open"}
}

# --- HILFSFUNKTIONEN ---
def fix_time(time_str):
    if not time_str: return None
    clean_str = time_str.replace("Z", "").split("+")[0]
    return datetime.fromisoformat(clean_str) + timedelta(hours=2)

# Funktion, die die Daten für EINEN EINZIGEN Fahrer holt (wird gleich parallel gestartet)
def fetch_single_driver_data(driver, heute):
    d_id = driver.get('id')
    d_name = driver.get('name', 'Unbekannt')
    tour_url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{d_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        res = requests.get(tour_url, timeout=5) # Max 5 Sekunden warten pro Fahrer
        if res.status_code == 200:
            data = res.json()
            gesamt_stopps = sum(r.get("numTotalOrders", 0) for r in data.get("routes", []))
            geliefert = sum(r.get("numDeliveredOrders", 0) for r in data.get("routes", []))
            status = "Aktiv" if gesamt_stopps > 0 else "Keine Tour"
            return {"Fahrer-ID": d_id, "Name": d_name, "Gesamt Stopps": gesamt_stopps, "Geliefert": geliefert, "Offen": gesamt_stopps - geliefert, "Status": status}
    except Exception:
        pass
    
    # Wenn er keine Tour hat oder ein Fehler aufgetreten ist
    return {"Fahrer-ID": d_id, "Name": d_name, "Gesamt Stopps": 0, "Geliefert": 0, "Offen": 0, "Status": "Keine Tour"}


@st.cache_data(ttl=60)
def load_all_driver_data():
    drivers_url = f"{SUPABASE_URL}/rest/v1/drivers?select=id,name"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        drivers_response = requests.get(drivers_url, headers=headers).json()
    except Exception:
        return []
    if not drivers_response:
        return []

    admin_data = []
    total_drivers = len(drivers_response)
    heute = datetime.now().strftime('%Y-%m-%d')
    
    my_bar = st.progress(0, text=f"Lade {total_drivers} Fahrer gleichzeitig...")

    # NEU: Hier laden wir 20 Fahrer gleichzeitig statt alle nacheinander!
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Startet alle Anfragen parallel
        futures = {executor.submit(fetch_single_driver_data, driver, heute): driver for driver in drivers_response}
        
        erledigt = 0
        for future in concurrent.futures.as_completed(futures):
            erledigt += 1
            # Update Ladebalken
            my_bar.progress(erledigt / total_drivers, text=f"Lade Daten... ({erledigt}/{total_drivers})")
            
            result = future.result()
            if result:
                admin_data.append(result)

    my_bar.empty()
    return admin_data


# --- SESSION STATE ---
if "logged_in" not in st.session_state: 
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = ""

# --- LOGIN BEREICH ---
if not st.session_state.logged_in:
    st.title("🚛 App Login")
    uid = st.text_input("ID")
    pwd = st.text_input("Passwort", type="password")
    
    if st.button("Anmelden"):
        clean_uid = uid.strip()
        clean_pwd = pwd.strip()
        
        # 1. Prüfen, ob es der Admin ist
        if clean_uid == "99999" and clean_pwd == "3300":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.rerun()
        else:
            # 2. Wenn nicht Admin, in Supabase nach Fahrer suchen
            url = f"{SUPABASE_URL}/rest/v1/drivers?id=eq.{clean_uid}&passwort=eq.{clean_pwd}"
            headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
            try:
                response = requests.get(url, headers=headers).json()
                if response:
                    st.session_state.logged_in = True
                    st.session_state.role = "driver"
                    st.session_state.driver_id = str(clean_uid)
                    st.session_state.driver_name = response[0].get('name', 'Fahrer')
                    st.rerun()
                else:
                    st.error("ID oder Passwort falsch.")
            except Exception as e:
                st.error("Fehler bei der Verbindung zur Datenbank.")

# --- ADMIN DASHBOARD ---
elif st.session_state.role == "admin":
    with st.sidebar:
        st.subheader("Admin Menü")
        if st.button("🚪 Ausloggen"):
            st.session_state.logged_in = False
            st.session_state.role = ""
            st.rerun()

    st.title("📊 Zentrales Admin-Dashboard")
    heute_str = datetime.now().strftime('%Y-%m-%d')
    st.subheader(f"Tagesübersicht für den {datetime.now().strftime('%d.%m.%Y')}")

    if st.button("🔄 Alle Daten aktualisieren"):
        st.cache_data.clear() 
        st.rerun()

    st.write("---")
    data = load_all_driver_data()

    if data:
        df = pd.DataFrame(data)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Fahrer im Einsatz", len(df[df["Status"] == "Aktiv"]))
        col2.metric("Stopps Gesamt", df["Gesamt Stopps"].sum())
        col3.metric("Geliefert", df["Geliefert"].sum())
        col4.metric("Noch Offen", df["Offen"].sum())
        
        st.write("---")
        # Große Tabelle anzeigen
        st.dataframe(df.sort_values(by="Offen", ascending=False), use_container_width=True, hide_index=True)
        
        # --- NEU: LUPE FÜR EINZELNE FAHRER ---
        st.write("---")
        st.subheader("🔍 Detailansicht: Einzelne Fahrer")
        
        # Dropdown-Menü Liste erstellen
        driver_dict = {f"{row['Name']} (ID: {row['Fahrer-ID']})": row['Fahrer-ID'] for row in data}
        
        selected_driver_name = st.selectbox(
            "Wähle einen Fahrer aus, um seine Tour im Detail zu sehen:", 
            ["Bitte wählen..."] + list(driver_dict.keys())
        )
        
        if selected_driver_name != "Bitte wählen...":
            selected_id = driver_dict[selected_driver_name]
            t = TRANSLATIONS["Deutsch"] # Admin sieht Details auf Deutsch
            
            detail_url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{selected_id}/{heute_str}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
            
            try:
                res_detail = requests.get(detail_url)
                if res_detail.status_code == 200:
                    routes = res_detail.json().get("routes", [])
                    if not routes:
                        st.info("Dieser Fahrer hat heute keine Touren geplant.")
                    else:
                        for route in routes:
                            st.markdown(f'<div class="stats-bar"><div>{t["Stopps"]}: {route.get("numTotalOrders")}</div><div>{t["Geliefert"]}: {route.get("numDeliveredOrders")}</div></div>', unsafe_allow_html=True)
                            html_list = ""
                            for cp in route.get("checkpoints", []):
                                an = fix_time(cp.get('realArrivalTime'))
                                start = fix_time(cp.get('deliverSince'))
                                ende = fix_time(cp.get('deliverTill'))
                                
                                status_text = t["Offen"]; color = "gray"
                                if an and start and ende:
                                    if an < start:
                                        status_text = f"{int((start - an).total_seconds() / 60)} {t['Früh']}"; color = "#0056b3"
                                    elif an > ende:
                                        status_text = f"{int((an - ende).total_seconds() / 60)} {t['Spät']}"; color = "#dc3545"
                                    else:
                                        status_text = t["Pünktlich"]; color = "#28a745"
                                
                                html_list += f'<div class="stop-card" style="border-left: 5px solid {color};"><div class="stop-address">{cp.get("address")}</div><div class="stop-times">{t["Fenster"]}: {start.strftime("%H:%M") if start else "--"}-{ende.strftime("%H:%M") if ende else "--"} | {t["Ist"]}: <b>{an.strftime("%H:%M") if an else "--"}</b></div><div class="stop-status" style="color: {color};">{status_text}</div></div>'
                            
                            col_space1, col_center, col_space3 = st.columns([1, 2, 1])
                            with col_center:
                                st.markdown(html_list, unsafe_allow_html=True)
                else:
                    st.error("Details konnten nicht geladen werden.")
            except Exception as e:
                 st.error(f"Fehler: {e}")

    else:
        st.info("Keine Daten gefunden. Haben die Fahrer heute Touren?")

# --- FAHRER DASHBOARD ---
elif st.session_state.role == "driver":
    with st.sidebar:
        if st.button("🚪 Ausloggen"):
            st.session_state.logged_in = False
            st.session_state.role = ""
            st.rerun()
            
    st.subheader(f"Hallo {st.session_state.driver_name} 👋")
    lang = st.selectbox("Sprache / Language", list(TRANSLATIONS.keys()))
    t = TRANSLATIONS[lang]
    
    heute = datetime.now().strftime('%Y-%m-%d')
    tour_url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        response = requests.get(tour_url)
        if response.status_code == 200:
            routes = response.json().get("routes", [])
            if not routes:
                st.info("Keine Touren für heute geplant.")
                
            for route in routes:
                st.markdown(f'<div class="stats-bar"><div>{t["Stopps"]}: {route.get("numTotalOrders")}</div><div>{t["Geliefert"]}: {route.get("numDeliveredOrders")}</div></div>', unsafe_allow_html=True)
                html_list = ""
                for cp in route.get("checkpoints", []):
                    an = fix_time(cp.get('realArrivalTime'))
                    start = fix_time(cp.get('deliverSince'))
                    ende = fix_time(cp.get('deliverTill'))
                    
                    status_text = t["Offen"]; color = "gray"
                    if an and start and ende:
                        if an < start:
                            status_text = f"{int((start - an).total_seconds() / 60)} {t['Früh']}"; color = "#0056b3"
                        elif an > ende:
                            status_text = f"{int((an - ende).total_seconds() / 60)} {t['Spät']}"; color = "#dc3545"
                        else:
                            status_text = t["Pünktlich"]; color = "#28a745"
                    
                    html_list += f'<div class="stop-card" style="border-left: 5px solid {color};"><div class="stop-address">{cp.get("address")}</div><div class="stop-times">{t["Fenster"]}: {start.strftime("%H:%M") if start else "--"}-{ende.strftime("%H:%M") if ende else "--"} | {t["Ist"]}: <b>{an.strftime("%H:%M") if an else "--"}</b></div><div class="stop-status" style="color: {color};">{status_text}</div></div>'
                st.markdown(html_list, unsafe_allow_html=True)
                
            st.write("---")
            if st.button("🔄 Daten aktualisieren"):
                st.rerun()
        else:
            st.error("Tourdaten konnten nicht geladen werden.")
    except Exception as e:
        st.error(f"Fehler bei der Verbindung zum Server: {e}")
