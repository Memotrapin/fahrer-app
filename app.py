import streamlit as st
import requests

st.set_page_config(page_title="Fahrer-App", layout="wide")

# Übersetzungen
TRANSLATIONS = {
    "Deutsch": {"Login": "Login", "Fahrer-ID": "Fahrer-ID", "Passwort": "Passwort", "Anmelden": "Anmelden", "Früh": "FRÜH", "Pünktlich": "PÜNKTLICH", "Spät": "SPÄT", "Offen": "OFFEN"},
    "English": {"Login": "Login", "Fahrer-ID": "Driver ID", "Passwort": "Password", "Anmelden": "Sign In", "Früh": "EARLY", "Pünktlich": "ON TIME", "Spät": "LATE", "Offen": "OPEN"},
    "Русский": {"Login": "Вход", "Fahrer-ID": "ID водителя", "Passwort": "Пароль", "Anmelden": "Войти", "Früh": "РАНО", "Pünktlich": "ВОВРЕМЯ", "Spät": "ПОЗДНО", "Offen": "ОТКРЫТО"},
    "Українська": {"Login": "Вхід", "Fahrer-ID": "ID водія", "Passwort": "Пароль", "Anmelden": "Увійти", "Früh": "РАНО", "Pünktlich": "ВЧАСНО", "Spät": "ПІЗНО", "Offen": "ВІДКРИТО"},
    "العربية": {"Login": "تسجيل الدخول", "Fahrer-ID": "معرف السائق", "Passwort": "كلمة المرور", "Anmelden": "دخول", "Früh": "مبكر", "Pünktlich": "في الموعد", "Spät": "متأخر", "Offen": "مفتوح"},
    "Türkçe": {"Login": "Giriş", "Fahrer-ID": "Sürücü ID", "Passwort": "Şifre", "Anmelden": "Giriş Yap", "Früh": "ERKEN", "Pünktlich": "ZAMANINDA", "Spät": "GEÇ", "Offen": "AÇIK"}
}

# Sprachwahl
lang = st.sidebar.selectbox("Sprache / Language", list(TRANSLATIONS.keys()))
t = TRANSLATIONS[lang]

# Styling
st.markdown("<style>.row { display: flex; align-items: center; border-bottom: 1px solid #ddd; padding: 10px 0; } .col-status { flex: 1; text-align: right; font-weight: bold; }</style>", unsafe_allow_html=True)

# Logik (Login & Dashboard)
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title(t["Login"])
    uid = st.text_input(t["Fahrer-ID"])
    pwd = st.text_input(t["Passwort"], type="password")
    if st.button(t["Anmelden"]):
        if uid == "13292" and pwd == "passwort123":
            st.session_state.logged_in = True
            st.rerun()
else:
    heute = "2026-06-09"
    url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/13292/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        data = requests.get(url).json()
        for route in data.get("routes", []):
            for cp in route.get("checkpoints", []):
                an = cp.get('realArrivalTime', '')
                if not an: status_text = t["Offen"]; color = "gray"
                elif an < cp.get('deliverSince', ''): status_text = t["Früh"]; color = "blue"
                elif an > cp.get('deliverTill', ''): status_text = t["Spät"]; color = "red"
                else: status_text = t["Pünktlich"]; color = "green"
                
                st.markdown(f'<div class="row"><div class="col-info"><b>{cp.get("address")}</b></div><div class="col-status" style="color:{color}">{status_text}</div></div>', unsafe_allow_html=True)
    except:
        st.error("Error")
