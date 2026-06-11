import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Fahrer-App", layout="centered")

# --- CSS für ein extrem kompaktes Design ---
st.markdown("""
    <style>
    .stApp { padding: 10px; }
    .status-bar { display: flex; justify-content: space-between; background: #eee; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-size: 12px; }
    .stop-line { border-bottom: 1px solid #ddd; padding: 5px 0; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (bleibt gleich) ---
FAHRER_LOGINS = {"13292": "passwort123"}
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚛 Login")
    uid = st.text_input("Fahrer-ID")
    pwd = st.text_input("Passwort", type="password")
    if st.button("Anmelden"):
        if uid in FAHRER_LOGINS and FAHRER_LOGINS[uid] == pwd:
            st.session_state.logged_in = True
            st.session_state.driver_id = uid
            st.rerun()
else:
    heute = "2026-06-09" # Zum Testen
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        data = requests.get(url).json()
        for route in data.get("routes", []):
            # KOMPAKTE STATUSLEISTE
            st.markdown(f"""
                <div class="status-bar">
                <span>Touren: <b>{len(data.get("routes", []))}</b></span>
                <span>Gesamt: <b>{route.get("numTotalOrders", 0)}</b></span>
                <span>Geliefert: <b>{route.get("numDeliveredOrders", 0)}</b></span>
                </div>
            """, unsafe_allow_html=True)
            
            # KOMPAKTE STOPP-LISTE
            for cp in route.get("checkpoints", []):
                an = cp.get('realArrivalTime', '')
                plan = cp.get('plannedArrivalTime', '')[11:16]
                ist = an[11:16] if an else "--"
                status = "✅" if an and an <= cp.get('deliverTill', '') else "⚠️" if an else "⏳"
                
                st.markdown(f"""
                    <div class="stop-line">
                    {status} <b>{cp.get('address')}</b><br>
                    <small>Zeit: {cp.get('deliverSince','')[11:16]}-{cp.get('deliverTill','')[11:16]} | Plan: {plan} | Ist: {ist}</small>
                    </div>
                """, unsafe_allow_html=True)
    except:
        st.error("Daten konnten nicht geladen werden.")
