import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- KONFIGURATION ---
SUPABASE_URL = "https://eytdvmenynabwltnryto.supabase.co"
SUPABASE_KEY = "DEIN_LANGER_PUBLISHABLE_KEY_HIER" # <--- HIER DEINEN KEY EINTRAGEN

# Admin-Dashboard nutzt die volle Bildschirmbreite (layout="wide")
st.set_page_config(page_title="Admin Dashboard", layout="wide")

st.title("📊 Zentrales Admin-Dashboard")
heute = datetime.now().strftime('%Y-%m-%d')
st.subheader(f"Tagesübersicht für den {heute}")

# --- DATEN ABRUFEN ---
@st.cache_data(ttl=60) # Speichert die Daten für 60 Sekunden zwischen, damit es schneller lädt
def load_all_driver_data():
    # 1. Alle Fahrer aus deiner Supabase 'drivers' Tabelle holen
    drivers_url = f"{SUPABASE_URL}/rest/v1/drivers?select=id,name"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    
    try:
        drivers_response = requests.get(drivers_url, headers=headers).json()
    except Exception as e:
        st.error("Konnte Fahrer nicht aus der Datenbank laden.")
        return []

    if not drivers_response:
        return []

    admin_data = []
    
    # Ladebalken für den Admin
    progress_text = "Lade Tourdaten der Fahrer..."
    my_bar = st.progress(0, text=progress_text)
    
    total_drivers = len(drivers_response)

    # 2. Für jeden Fahrer die Tourdaten vom Server abfragen
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
                
                # Nur Fahrer anzeigen, die heute eine Tour haben (oder alle, je nachdem was du willst)
                status = "Aktiv" if gesamt_stopps > 0 else "Keine Tour"
                
                admin_data.append({
                    "Fahrer-ID": d_id,
                    "Name": d_name,
                    "Gesamt Stopps": gesamt_stopps,
                    "Geliefert": geliefert,
                    "Offen": gesamt_stopps - geliefert,
                    "Status": status
                })
        except Exception as e:
            pass # Wenn ein Fehler bei einem Fahrer auftritt, einfach zum nächsten gehen
        
        # Ladebalken aktualisieren
        my_bar.progress((index + 1) / total_drivers, text=f"Lade Daten für {d_name}...")

    my_bar.empty() # Ladebalken entfernen, wenn fertig
    return admin_data

# --- ANZEIGE IM DASHBOARD ---
if st.button("🔄 Daten jetzt aktualisieren"):
    st.cache_data.clear() # Löscht den Zwischenspeicher und lädt hart neu
    st.rerun()

st.write("---")

data = load_all_driver_data()

if data:
    # Daten in eine saubere Tabelle (Pandas DataFrame) umwandeln
    df = pd.DataFrame(data)
    
    # 1. Kennzahlen ganz oben anzeigen
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
    
    # 2. Große, interaktive Tabelle anzeigen
    # Wir sortieren nach offenen Stopps, damit du siehst, wer noch am meisten zu tun hat
    df_sorted = df.sort_values(by="Offen", ascending=False)
    
    # Tabelle formatieren, sodass sie die ganze Breite einnimmt
    st.dataframe(
        df_sorted, 
        use_container_width=True,
        hide_index=True # Versteckt die unnötige Nummerierung links
    )
else:
    st.info("Keine Daten gefunden. Haben die Fahrer heute überhaupt Touren?")
