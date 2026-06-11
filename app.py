import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Fahrer-App", layout="wide")

# CSS für eine klare Tabellen-Optik
st.markdown("""
    <style>
    .row { display: flex; align-items: center; border-bottom: 1px solid #ddd; padding: 10px 0; font-size: 14px; }
    .col-info { flex: 4; }
    .col-status { flex: 1; text-align: right; font-weight: bold; }
    .früh { color: blue; }
    .pünktlich { color: green; }
    .spät { color: red; }
    </style>
    """, unsafe_allow_html=True)

# ... (Login bleibt wie gehabt) ...
# Gehe direkt zum Dashboard-Teil:

    heute = "2026-06-09" 
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        data = requests.get(url).json()
        for route in data.get("routes", []):
            st.write(f"### 🚛 Tour {route.get('id')} | {route.get('numDeliveredOrders')}/{route.get('numTotalOrders')} Stopps")
            
            for cp in route.get("checkpoints", []):
                an = cp.get('realArrivalTime', '')
                start = cp.get('deliverSince', '')[11:16]
                ende = cp.get('deliverTill', '')[11:16]
                
                # Status Logik
                if not an: 
                    status_text = "OFFEN"
                    css_class = ""
                elif an < cp.get('deliverSince', ''):
                    status_text = "FRÜH"
                    css_class = "früh"
                elif an > cp.get('deliverTill', ''):
                    status_text = "SPÄT"
                    css_class = "spät"
                else:
                    status_text = "PÜNKTLICH"
                    css_class = "pünktlich"

                # Aufbau der Zeile
                st.markdown(f"""
                    <div class="row">
                        <div class="col-info">
                            <b>{cp.get('address')}</b><br>
                            <small>Zeitfenster: {start}-{ende} | Ankunft: {an[11:16] if an else '--'}</small>
                        </div>
                        <div class="col-status {css_class}">{status_text}</div>
                    </div>
                """, unsafe_allow_html=True)
    except:
        st.error("Daten konnten nicht geladen werden.")
