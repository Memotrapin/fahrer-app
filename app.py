import streamlit as st
import requests
from datetime import datetime

# --- MODERNES DESIGN (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .css-1r6slp0 { padding: 2rem; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    div.stButton > button { border-radius: 20px; background-color: #007bff; color: white; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.set_page_config(page_title="Driver Dashboard", layout="centered")

# --- LOGIN LOGIK ---
FAHRER_LOGINS = {"13292": "passwort123"}
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚛 Logistik Portal")
    st.write("Bitte melde dich mit deiner Fahrer-ID an.")
    uid = st.text_input("Fahrer-ID")
    pwd = st.text_input("Passwort", type="password")
    if st.button("Anmelden"):
        if uid in FAHRER_LOGINS and FAHRER_LOGINS[uid] == pwd:
            st.session_state.logged_in = True
            st.session_state.driver_id = uid
            st.rerun()
else:
    # --- MODERNES DASHBOARD ---
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.title(f"Moin, Fahrer {st.session_state.driver_id}! 👋")
    
    heute = datetime.now().strftime('%Y-%m-%d')
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        data = requests.get(url).json()
        routes = data.get("routes", [])
        
        if not routes: st.warning("Heute liegen keine Touren vor.")
        
        for r in routes:
            with st.container():
                st.markdown(f"### 📍 Tour {r.get('id')}")
                col1, col2 = st.columns(2)
                col1.metric("Gesamtstopps", r.get("numTotalOrders"))
                col2.metric("Erledigt", r.get("numDeliveredOrders"))
                
                for cp in r.get("checkpoints", []):
                    # Zeit-Logik
                    start, ende = cp.get('deliverSince'), cp.get('deliverTill')
                    status = "✅ Pünktlich" if cp.get('realArrivalTime') and cp.get('realArrivalTime') <= ende else "⚠️ Überprüfen"
                    
                    with st.expander(f"📦 Stopp {cp.get('position')}: {cp.get('address')[:20]}..."):
                        st.write(f"**Zeitfenster:** {start[11:16]} - {ende[11:16]}")
                        st.info(f"Status: {status}")
                        if st.button(f"Ankunft bestätigen", key=cp.get('id')):
                            st.success("Ankunft wurde übermittelt!")
    except Exception as e:
        st.error("Daten konnten nicht geladen werden.")
