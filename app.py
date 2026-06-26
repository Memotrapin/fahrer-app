import streamlit as st
import requests
import pandas as pd
import concurrent.futures
from datetime import datetime, timedelta

# --- KONFIGURATION ---
SUPABASE_URL = "https://uftplslamjbbhlozsygo.supabase.co" # Korrigierte URL für API-Zugriffe
SUPABASE_KEY = "sb_publishable_2ylpUDTGGt9CfCW-75nwDg_j6ChUpgP" 

st.set_page_config(page_title="Fahrer & Admin App", layout="wide")

# --- HILFSFUNKTIONEN ---
def fix_time(time_str):
    if not time_str: return None
    try:
        clean_str = time_str.replace("Z", "").split("+")[0]
        return datetime.fromisoformat(clean_str) + timedelta(hours=2)
    except: return None

def get_status(an, start, ende):
    if not an: return "⚪ Offen"
    if an < start: return f"🔵 Früh ({int((start - an).total_seconds() / 60)} min)"
    if an > ende: return f"🔴 Spät ({int((an - ende).total_seconds() / 60)} min)"
    return "🟢 Pünktlich"

def fetch_single_driver_data(d, heute):
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{d['id']}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    try:
        res = requests.get(url, timeout=5).json()
        routes = res.get("routes", [])
        total = sum(r.get("numTotalOrders", 0) for r in routes)
        done = sum(r.get("numDeliveredOrders", 0) for r in routes)
        return {"Fahrer-ID": d['id'], "Name": d['name'], "Touren": len(routes), "Gesamt Stopps": total, "Geliefert": done, "Offen": total - done, "Status": "Aktiv" if total > 0 else "Leer"}
    except: return {"Fahrer-ID": d['id'], "Name": d['name'], "Touren": 0, "Gesamt Stopps": 0, "Geliefert": 0, "Offen": 0, "Status": "Leer"}

# --- LOGIN & SESSION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "role" not in st.session_state: st.session_state.role = ""

if not st.session_state.logged_in:
    st.title("🚛 Login")
    uid = st.text_input("ID")
    pwd = st.text_input("Passwort", type="password")
    if st.button("Anmelden"):
        if uid == "99999" and pwd == "3300":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.rerun()
        else:
            url = f"https://eytdvmenynabwltnryto.supabase.co/rest/v1/drivers?id=eq.{uid.strip()}&passwort=eq.{pwd.strip()}"
            headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
            try:
                response = requests.get(url, headers=headers).json()
                if response:
                    st.session_state.logged_in = True
                    st.session_state.role = "driver"
                    st.session_state.driver_id = str(uid.strip())
                    st.session_state.driver_name = response[0].get('name', 'Fahrer')
                    st.rerun()
                else: st.error("ID oder Passwort falsch.")
            except: st.error("Verbindungsfehler.")

# --- ADMIN DASHBOARD ---
elif st.session_state.role == "admin":
    st.title("📊 Admin-Dashboard")
    if st.button("🔄 Aktualisieren"): st.cache_data.clear(); st.rerun()
    
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    drivers = requests.get(f"https://eytdvmenynabwltnryto.supabase.co/rest/v1/drivers?select=id,name", headers=headers).json()
    heute = datetime.now().strftime('%Y-%m-%d')
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        data = list(executor.map(lambda d: fetch_single_driver_data(d, heute), drivers))
    
    df = pd.DataFrame(data)
    col_table, col_details = st.columns([1.5, 1])
    with col_table:
        event = st.dataframe(df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
    
    with col_details:
        if event.selection.rows:
            row = df.iloc[event.selection.rows[0]]
            st.subheader(f"🔍 {row['Name']}")
            try:
                res = requests.get(f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{row['Fahrer-ID']}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47").json()
                for idx, route in enumerate(res.get("routes", []), 1):
                    st.markdown(f"**🚚 Tour {idx}**")
                    stops = []
                    for cp in route.get("checkpoints", []):
                        an = fix_time(cp.get('realArrivalTime'))
                        s, e = fix_time(cp.get('deliverSince')), fix_time(cp.get('deliverTill'))
                        stops.append({"Adresse": cp.get("address"), "Fenster": f"{s.strftime('%H:%M') if s else '--'}-{e.strftime('%H:%M') if e else '--'}", "Ist": an.strftime('%H:%M') if an else "--", "Status": get_status(an, s, e)})
                    st.dataframe(pd.DataFrame(stops), use_container_width=True, hide_index=True)
            except: st.error("Fehler beim Laden")

# --- FAHRER DASHBOARD ---
elif st.session_state.role == "driver":
    if st.button("🚪 Ausloggen"): st.session_state.logged_in = False; st.rerun()
    st.subheader(f"Hallo {st.session_state.driver_name} 👋")
    heute = datetime.now().strftime('%Y-%m-%d')
    try:
        res = requests.get(f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47").json()
        for idx, route in enumerate(res.get("routes", []), 1):
            st.markdown(f"**🚚 Tour {idx}**")
            stops = []
            for cp in route.get("checkpoints", []):
                an = fix_time(cp.get('realArrivalTime'))
                s, e = fix_time(cp.get('deliverSince')), fix_time(cp.get('deliverTill'))
                stops.append({"Adresse": cp.get("address"), "Fenster": f"{s.strftime('%H:%M') if s else '--'}-{e.strftime('%H:%M') if e else '--'}", "Ist": an.strftime('%H:%M') if an else "--", "Status": get_status(an, s, e)})
            st.dataframe(pd.DataFrame(stops), use_container_width=True, hide_index=True)
    except: st.error("Fehler.")
