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
    except: st.error("Fehler.")
