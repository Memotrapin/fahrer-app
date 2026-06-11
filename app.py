import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Fahrer-Portal", layout="centered")

# --- LOGIN (bleibt gleich) ---
FAHRER_LOGINS = {"13292": "passwort123"}
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚛 Fahrer-Login")
    uid = st.text_input("Fahrer-ID")
    pwd = st.text_input("Passwort", type="password")
    if st.button("Anmelden"):
        if uid in FAHRER_LOGINS and FAHRER_LOGINS[uid] == pwd:
            st.session_state.logged_in = True
            st.session_state.driver_id = uid
            st.rerun()
else:
    # --- DASHBOARD ---
    heute = "2026-06-09" # Zum Testen
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        data = requests.get(url).json()
        routes = data.get("routes", [])
        
        # 1. GANZ OBEN: Anzahl der Touren
        st.metric("Gesamte Touren heute", len(routes))
        st.write("---")
        
        for route in routes:
            # 2. DARUNTER: Stopps Statistik
            col1, col2 = st.columns(2)
            col1.metric("Geplante Stopps", route.get("numTotalOrders", 0))
            col2.metric("Bereits geliefert", route.get("numDeliveredOrders", 0))
            st.write("---")
            
            # 3. ROUTEN-DETAILS
            st.subheader(f"Route {route.get('id')}")
            
            for cp in route.get("checkpoints", []):
                # Daten extrahieren
                adr = cp.get('address', 'Unbekannt')
                zf = f"{cp.get('deliverSince', '')[11:16]} - {cp.get('deliverTill', '')[11:16]}"
                plan = cp.get('plannedArrivalTime', '')[11:16]
                ist = cp.get('realArrivalTime', '')[11:16] if cp.get('realArrivalTime') else "-"
                
                # Status-Logik
                if not cp.get('realArrivalTime'): 
                    status = "⏳ Offen"
                elif cp.get('realArrivalTime') < cp.get('deliverSince', ''):
                    status = "🚀 Zu früh"
                elif cp.get('realArrivalTime') > cp.get('deliverTill', ''):
                    status = "⚠️ Verspätet"
                else:
                    status = "✅ Pünktlich"

                # DIE DÜNNE ZEILE:
                st.markdown(f"**{adr}**")
                st.caption(f"{zf} | Plan: {plan} | Ist: {ist} | **{status}**")
                st.write("") # Kleine Lücke
    except Exception as e:
        st.error("Daten konnten nicht geladen werden.")
