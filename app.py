import streamlit as st
import requests
import pandas as pd
import concurrent.futures
from datetime import datetime, timedelta

# --- KONFIGURATION ---
SUPABASE_URL = "https://eytdvmenynabwltnryto.supabase.co"
# TRAGE HIER DEINEN ECHTEN KEY EIN:
SUPABASE_KEY = "sb_publishable_2ylpUDTGGt9CfCW-75nwDg_j6ChUpgP" 

st.set_page_config(page_title="Fahrer & Admin App", layout="wide", initial_sidebar_state="collapsed")

# --- CSS ---
st.markdown("""
    <style>
    .block-container { padding: 10px; }
    .stats-bar { display: flex; justify-content: space-around; background: #222; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; font-size: 14px;}
    .stop-card { background: white; padding: 10px; margin-bottom: 8px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); display: flex; flex-direction: column; }
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

def fetch_single_driver_data(driver, heute):
    d_id = driver.get('id')
    d_name = driver.get('name', 'Unbekannt')
    tour_url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{d_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        res = requests.get(tour_url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            routes = data.get("routes", [])
            anzahl_touren = len(routes)
            gesamt_stopps = sum(r.get("numTotalOrders", 0) for r in routes)
            geliefert = sum(r.get("numDeliveredOrders", 0) for r in routes)
            status = "Aktiv" if gesamt_stopps > 0 else "Keine Tour"
            return {"Fahrer-ID": d_id, "Name": d_name, "Touren": anzahl_touren, "Gesamt Stopps": gesamt_stopps, "Geliefert": geliefert, "Offen": gesamt_stopps - geliefert, "Status": status}
    except Exception: pass
    return {"Fahrer-ID": d_id, "Name": d_name, "Touren": 0, "Gesamt Stopps": 0, "Geliefert": 0, "Offen": 0, "Status": "Keine Tour"}

@st.cache_data(ttl=60)
def load_all_driver_data():
    drivers_url = f"{SUPABASE_URL}/rest/v1/drivers?select=id,name"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try: drivers_response = requests.get(drivers_url, headers=headers).json()
    except Exception: return []
    if not drivers_response: return []

    admin_data = []
    total_drivers = len(drivers_response)
    heute = datetime.now().strftime('%Y-%m-%d')
    my_bar = st.progress(0, text=f"Lade {total_drivers} Fahrer...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_single_driver_data, driver, heute): driver for driver in drivers_response}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            my_bar.progress((i+1) / total_drivers)
            result = future.result()
            if result: admin_data.append(result)
    my_bar.empty()
    return admin_data

# --- SESSION & LOGIN ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "role" not in st.session_state: st.session_state.role = ""

if not st.session_state.logged_in:
    st.title("🚛 App Login")
    uid = st.text_input("ID")
    pwd = st.text_input("Passwort", type="password")
    if st.button("Anmelden"):
        if uid == "99999" and pwd == "3300":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.rerun()
        else:
            url = f"{SUPABASE_URL}/rest/v1/drivers?id=eq.{uid.strip()}&passwort=eq.{pwd.strip()}"
            headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
            try:
                response = requests.get(url, headers=headers).json()
                if response:
                    st.session_state.logged_in = True
                    st.session_state.role = "driver"
                    st.session_state.driver_id = str(uid.strip())
                    st.session_state.driver_name = response[0].get('name', 'Fahrer')
                    st.rerun()
            except: st.error("Login fehlgeschlagen.")

# --- ADMIN DASHBOARD ---
elif st.session_state.role == "admin":
    st.title("📊 Zentrales Admin-Dashboard")
    if st.button("🔄 Aktualisieren"): st.cache_data.clear(); st.rerun()
    
    data = load_all_driver_data()
    if data:
        df = pd.DataFrame(data)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Fahrer", len(df[df["Status"] == "Aktiv"]))
        c2.metric("Touren", df["Touren"].sum())
        c3.metric("Stopps", df["Gesamt Stopps"].sum())
        c4.metric("Geliefert", df["Geliefert"].sum())
        c5.metric("Offen", df["Offen"].sum())
        
        col_table, col_details = st.columns([1.5, 1])
        with col_table:
            event = st.dataframe(df.sort_values(by="Offen", ascending=False), use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
        
        with col_details:
            if event.selection.rows:
                row = df.sort_values(by="Offen", ascending=False).iloc[event.selection.rows[0]]
                st.subheader(f"🔍 {row['Name']}")
                heute = datetime.now().strftime('%Y-%m-%d')
                url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{row['Fahrer-ID']}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
                try:
                    res = requests.get(url).json()
                    for idx, route in enumerate(res.get("routes", []), 1):
                        st.markdown(f"**🚚 Tour {idx}**")
                        stops = []
                        for cp in route.get("checkpoints", []):
                            an = fix_time(cp.get('realArrivalTime'))
                            s, e = fix_time(cp.get('deliverSince')), fix_time(cp.get('deliverTill'))
                            status = "🟢 Pünktlich" if not an else ("🔴 Spät" if an > e else "🔵 Früh")
                            stops.append({"Adresse": cp.get("address"), "Fenster": f"{s.strftime('%H:%M') if s else '--'}-{e.strftime('%H:%M') if e else '--'}", "Ist": an.strftime('%H:%M') if an else "--", "Status": status})
                        st.dataframe(pd.DataFrame(stops), use_container_width=True, hide_index=True)
                except: st.error("Datenfehler")

# --- FAHRER DASHBOARD ---
elif st.session_state.role == "driver":
    st.subheader(f"Hallo {st.session_state.driver_name} 👋")
    heute = datetime.now().strftime('%Y-%m-%d')
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    try:
        res = requests.get(url).json()
        for route in res.get("routes", []):
            for cp in route.get("checkpoints", []):
                st.markdown(f'<div class="stop-card">{cp.get("address")}</div>', unsafe_allow_html=True)
    except: st.error("Fehler.")import streamlit as st
import requests
import pandas as pd
import concurrent.futures
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

def fetch_single_driver_data(driver, heute):
    d_id = driver.get('id')
    d_name = driver.get('name', 'Unbekannt')
    tour_url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{d_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        res = requests.get(tour_url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            routes = data.get("routes", [])
            anzahl_touren = len(routes)
            gesamt_stopps = sum(r.get("numTotalOrders", 0) for r in routes)
            geliefert = sum(r.get("numDeliveredOrders", 0) for r in routes)
            status = "Aktiv" if gesamt_stopps > 0 else "Keine Tour"
            
            return {
                "Fahrer-ID": d_id, 
                "Name": d_name, 
                "Touren": anzahl_touren,  # <-- NEUE SPALTE HIER
                "Gesamt Stopps": gesamt_stopps, 
                "Geliefert": geliefert, 
                "Offen": gesamt_stopps - geliefert, 
                "Status": status
            }
    except Exception:
        pass
    
    return {"Fahrer-ID": d_id, "Name": d_name, "Touren": 0, "Gesamt Stopps": 0, "Geliefert": 0, "Offen": 0, "Status": "Keine Tour"}

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

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_single_driver_data, driver, heute): driver for driver in drivers_response}
        erledigt = 0
        for future in concurrent.futures.as_completed(futures):
            erledigt += 1
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
        
        if clean_uid == "99999" and clean_pwd == "3300":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.rerun()
        else:
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
        
        # --- KENNZAHLEN OBEN (Jetzt mit Touren!) ---
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Fahrer im Einsatz", len(df[df["Status"] == "Aktiv"]))
        col2.metric("Touren Gesamt", df["Touren"].sum())
        col3.metric("Stopps Gesamt", df["Gesamt Stopps"].sum())
        col4.metric("Geliefert", df["Geliefert"].sum())
        col5.metric("Noch Offen", df["Offen"].sum())
        
        st.write("---")
        st.markdown("👇 **Klicke auf eine Zeile in der linken Tabelle**, um die Details des Fahrers auf der rechten Seite zu sehen!")
        
        # Split-Screen Layout
        col_table, col_details = st.columns([1.5, 1]) 
        
        df_sorted = df.sort_values(by="Offen", ascending=False).reset_index(drop=True)
        
        with col_table:
            event = st.dataframe(
                df_sorted, 
                use_container_width=True, 
                hide_index=True,
                on_select="rerun",           
                selection_mode="single-row"  
            )
        
        with col_details:
            selected_rows = event.selection.rows
            
            if selected_rows:
                row_idx = selected_rows[0]
                selected_id = df_sorted.iloc[row_idx]["Fahrer-ID"]
                selected_name = df_sorted.iloc[row_idx]["Name"]
                
                st.info(f"**🔍 Details für: {selected_name}**")
                
                detail_url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{selected_id}/{heute_str}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
                
                try:
                    res_detail = requests.get(detail_url)
                    if res_detail.status_code == 200:
                        routes = res_detail.json().get("routes", [])
                        if not routes:
                            st.warning("Dieser Fahrer hat heute keine Touren.")
                        else:
                            drv_touren = len(routes)
                            drv_stopps = sum(r.get("numTotalOrders", 0) for r in routes)
                            drv_geliefert = sum(r.get("numDeliveredOrders", 0) for r in routes)
                            
                            st.write(f"🚚 **Touren:** {drv_touren} | 📦 **Stopps:** {drv_stopps} | ✅ **Geliefert:** {drv_geliefert}")
                            st.write("---") 
                            
                            # --- NEU: TOUREN SAUBER TRENNEN ---
                            for idx, route in enumerate(routes, start=1):
                                st.markdown(f"**🚚 Tour {idx}**") # Überschrift für jede Tour
                                
                                stops_data = []
                                for cp in route.get("checkpoints", []):
                                    an = fix_time(cp.get('realArrivalTime'))
                                    start = fix_time(cp.get('deliverSince'))
                                    ende = fix_time(cp.get('deliverTill'))
                                    
                                    status_text = "⚪ Offen"
                                    if an and start and ende:
                                        if an < start:
                                            status_text = f"🔵 Früh ({int((start - an).total_seconds() / 60)} min)"
                                        elif an > ende:
                                            status_text = f"🔴 Spät ({int((an - ende).total_seconds() / 60)} min)"
                                        else:
                                            status_text = "🟢 Pünktlich"
                                    
                                    stops_data.append({
                                        "Adresse": cp.get("address", "Unbekannt"),
                                        "Ist-Zeit": an.strftime('%H:%M') if an else "--",
                                        "Status": status_text
                                    })
                                
                                if stops_data:
                                    df_stops = pd.DataFrame(stops_data)
                                    st.dataframe(df_stops, use_container_width=True, hide_index=True)
                                else:
                                    st.write("Keine Stopp-Daten für diese Tour gefunden.")
                                    
                                st.write("") # Kleiner Platzhalter zwischen zwei Touren
                                
                    else:
                        st.error("Details konnten nicht geladen werden.")
                except Exception as e:
                     st.error(f"Fehler: {e}")
            else:
                st.info("👈 Bitte klicke links auf einen Fahrer, um hier seine Zeiten und Touren zu sehen.")

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
