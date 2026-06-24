import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- KONFIGURATION ---
SUPABASE_URL = "https://eytdvmenynabwltnryto.supabase.co"
SUPABASE_KEY = "sb_publishable_2ylpUDTGGt9CfCW-75nwDg_j6ChUpgP" # <--- HIER DEINEN KEY EINTRAGEN

# Admin-Dashboard nutzt die volle Bildschirmbreite
st.set_page_config(page_title="Admin Dashboard", layout="wide")

# --- FUNKTIONEN ---
# Wir definieren die Lade-Funktion ganz oben
@st.cache_data(ttl=60)
def load_all_driver_data():
    drivers_url = f"{SUPABASE_URL}/rest/v1/drivers?select=id,name"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    
    try:
        drivers_response = requests.get(drivers_url, headers=headers).json()
    except Exception:
        st.error("Konnte Fahrer nicht aus der Datenbank laden.")
        return []

    if not drivers_response:
        return []

    admin_data = []
    progress_text = "Lade Tourdaten der Fahrer..."
    my_bar = st.progress(0, text=progress_text)
    total_drivers = len(drivers_response)

    heute = datetime.now().strftime('%Y-%m-%d')

    for index, driver in enumerate(drivers_response):
        d_id = driver.get('id')
        d_name = driver.get('name', 'Unbekannt')
        
        tour_url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{d_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
        
        try:
            res = requests.get(tour_url)
            if res.status_code == 200:
                data = res.json()
                routes = data.get("routes", [])
                
                gesamt_stopps = 0
                geliefert = 0
                
                for route in routes:
                    gesamt_stopps += route.get("numTotalOrders", 0)
                    geliefert += route.get("numDeliveredOrders", 0)
                
                status = "Aktiv" if gesamt_stopps > 0 else "Keine Tour"
                
                admin_data.append({
                    "Fahrer-ID": d_id,
                    "Name": d_name,
                    "Gesamt Stopps": gesamt_stopps,
                    "Geliefert": geliefert,
                    "Offen": gesamt_stopps - geliefert,
                    "Status": status
                })
        except Exception:
            pass 
        
        my_bar.progress((index + 1) / total_drivers, text=f"Lade Daten für {d_name}...")

    my_bar.empty()
    return admin_data


# --- LOGIN STATUS PRÜFEN ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# --- LOGIN BEREICH ---
if not st.session_state.admin_logged_in:
    st.title("🔐 Admin-Login")
    st.markdown("Bitte melde dich an, um auf das zentrale Dashboard zuzugreifen.")
    
    admin_id = st.text_input("Admin-ID")
    admin_pwd = st.text_input("Passwort", type="password")
    
    if st.button("Anmelden"):
        # Hier sind deine Zugangsdaten hinterlegt
        if admin_id == "99999" and admin_pwd == "3300":
            st.session_state.admin_logged_in = True
            st.rerun()
        else:
            st.error("ID oder Passwort falsch!")

# --- DASHBOARD BEREICH ---
else:
    # Sidebar mit Logout-Button
    with st.sidebar:
        st.subheader("Admin Menü")
        if st.button("🚪 Ausloggen"):
            st.session_state.admin_logged_in = False
            st.rerun()

    # Dashboard Header
    st.title("📊 Zentrales Admin-Dashboard")
    heute_anzeige = datetime.now().strftime('%d.%m.%Y')
    st.subheader(f"Tagesübersicht für den {heute_anzeige}")

    if st.button("🔄 Daten jetzt aktualisieren"):
        st.cache_data.clear() 
        st.rerun()

    st.write("---")

    # Daten laden und anzeigen
    data = load_all_driver_data()

    if data:
        df = pd.DataFrame(data)
        
        stopps_total = df["Gesamt Stopps"].sum()
        geliefert_total = df["Geliefert"].sum()
        offen_total = df["Offen"].sum()
        aktive_fahrer = len(df[df["Status"] == "Aktiv"])
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Fahrer im Einsatz", aktive_fahrer)
        col2.metric("Stopps Gesamt", stopps_total)
        col3.metric("Geliefert", geliefert_total)
        col4.metric("Noch Offen", offen_total)
        
        st.write("---")
        
        df_sorted = df.sort_values(by="Offen", ascending=False)
        
        st.dataframe(
            df_sorted, 
            use_container_width=True,
            hide_index=True 
        )
    else:
        st.info("Keine Daten gefunden. Haben die Fahrer heute überhaupt Touren?")
