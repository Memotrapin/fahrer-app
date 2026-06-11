import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Fahrer-Portal", layout="wide")

# ... (Login Bereich bleibt gleich) ...

else:
    st.title(f"Hallo Fahrer {st.session_state.driver_id}!")
    heute = datetime.now().strftime('%Y-%m-%d')
    
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for route in data.get("routes", []):
                # --- NEU: Zusammenfassung der Tour-Daten ---
                with st.expander(f"📍 Tour {route.get('id')} - Übersicht", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Pakete", route.get("numTotalOrders", 0))
                    c2.metric("Geliefert", route.get("numDeliveredOrders", 0))
                    c3.metric("Verspätet", route.get("numDelayedOrdersPlan", 0))
                    
                    st.divider()
                    
                    # --- Details der Stopps ---
                    for cp in route.get("checkpoints", []):
                        start = cp.get('deliverSince', '00:00')[11:16]
                        ende = cp.get('deliverTill', '23:59')[11:16]
                        an = cp.get('realArrivalTime', '-')[11:16] if cp.get('realArrivalTime') else "-"
                        
                        status = "✅"
                        if cp.get('realArrivalTime') and cp.get('realArrivalTime') > cp.get('deliverTill', ''):
                            status = "⚠️"
                        
                        st.markdown(f"**{status} {cp.get('address')}**")
                        st.caption(f"Fenster: {start}-{ende} | Ankunft: {an}")
        else:
            st.error("Keine Daten gefunden.")
    except Exception as e:
        st.error(f"Fehler: {e}")
