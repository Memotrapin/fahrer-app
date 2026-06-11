import streamlit as st
import requests
from datetime import datetime

# Seiten-Konfiguration
st.set_page_config(page_title="Fahrer-Portal", layout="wide")

# Session-Status für Login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.driver_id = ""

# --- Login Seite ---
if not st.session_state.logged_in:
    st.title("🚛 Fahrer-Login")
    input_id = st.text_input("Bitte Fahrer-ID eingeben")
    if st.button("Anmelden"):
        if input_id:
            st.session_state.driver_id = input_id
            st.session_state.logged_in = True
            st.rerun() # Seite neu laden
        else:
            st.warning("Bitte gib eine gültige ID ein.")

# --- Dashboard Seite ---
else:
    st.sidebar.button("Abmelden", on_click=lambda: st.session_state.update({"logged_in": False}))
    
    st.title(f"Hallo Fahrer {st.session_state.driver_id}!")
    st.subheader(f"Deine Touren für heute: {datetime.now().strftime('%d.%m.%Y')}")
    
    # Automatisch das Datum von heute
    datum = datetime.now().strftime('%Y-%m-%d')
    org_id = "b993a325-6d34-4af5-a955-3d0b5e07cd47"
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{datum}?organizationId={org_id}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Daten abrufen
        routes = data.get("routes", [])
        if not routes:
            st.info("Keine Touren für heute gefunden.")
        
        for route in routes:
            with st.expander(f"Tour {route.get('id')} | Status: {route.get('numDeliveredOrders')} erledigt", expanded=True):
                table_data = []
                for cp in route.get("checkpoints", []):
                    an = cp.get('realArrivalTime')
                    start = cp.get('deliverSince')
                    ende = cp.get('deliverTill')
                    
                    status = "✅ Pünktlich"
                    if an and start and ende:
                        if an < start: status = "🚀 Zu früh"
                        elif an > ende: status = "⚠️ Zu spät"
                            
                    table_data.append({
                        "Adresse": cp.get('address'),
                        "Fenster": f"{start[11:16]}-{ende[11:16]}",
                        "Ankunft": an[11:16] if an else "-",
                        "Status": status
                    })
                st.table(table_data)
                
    except Exception as e:
        st.error("Daten konnten nicht geladen werden. Bitte später versuchen.")