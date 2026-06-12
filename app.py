# --- FAHRER-DASHBOARD ---
else:
    # Ausloggen-Button in der ausklappbaren Sidebar links platzieren
    with st.sidebar:
        if st.button("🚪 Ausloggen"):
            st.session_state.logged_in = False
            st.session_state.driver_id = ""
            st.session_state.driver_name = ""
            st.rerun()
            
    # Begrüßung des Fahrers ganz oben
    st.subheader(f"Hallo {st.session_state.driver_name} 👋")
    
    # Sprachauswahl unter der Begrüßung
    lang = st.selectbox("Sprache / Language", list(TRANSLATIONS.keys()))
    t = TRANSLATIONS[lang]
    
    # Heutiges Datum holen und Touren-API abfragen
    heute = datetime.now().strftime('%Y-%m-%d')
    tour_url = f"https://uftplslamjbbhlozsygo.supabase.co/functions/v1/fetch-drivers-detail/{st.session_state.driver_id}/{heute}?organizationId=b993a325-6d34-4af5-a955-3d0b5e07cd47"
    
    try:
        response = requests.get(tour_url)
        if response.status_code == 200:
            data = response.json()
            routes = data.get("routes", [])
            
            # WICHTIG: Wenn die Liste leer ist, zeigen wir das an!
            if not routes:
                st.info("Keine Touren für heute geplant.")
                
            for route in routes:
                # Statistik-Balken oben (Stopps und gelieferte Pakete)
                st.markdown(f'<div class="stats-bar"><div>{t["Stopps"]}: {route.get("numTotalOrders")}</div><div>{t["Geliefert"]}: {route.get("numDeliveredOrders")}</div></div>', unsafe_allow_html=True)
                
                html_list = ""
                for cp in route.get("checkpoints", []):
                    an = fix_time(cp.get('realArrivalTime'))
                    start = fix_time(cp.get('deliverSince'))
                    ende = fix_time(cp.get('deliverTill'))
                    
                    status_text = t["Offen"]; color = "gray"
                    if an and start and ende:
                        if an < start:
                            diff = int((start - an).total_seconds() / 60)
                            status_text = f"{diff} {t['Früh']}"; color = "#0056b3"
                        elif an > ende:
                            diff = int((an - ende).total_seconds() / 60)
                            status_text = f"{diff} {t['Spät']}"; color = "#dc3545"
                        else:
                            status_text = t["Pünktlich"]; color = "#28a745"
                    
                    # Einzelne Adresskarte zusammenbauen
                    html_list += f"""
                    <div class="stop-card" style="border-left: 5px solid {color};">
                        <div class="stop-address">{cp.get('address')}</div>
                        <div class="stop-times">{t['Fenster']}: {start.strftime("%H:%M") if start else '--'}-{ende.strftime("%H:%M") if ende else '--'} | {t['Ist']}: <b>{an.strftime("%H:%M") if an else '--'}</b></div>
                        <div class="stop-status" style="color: {color};">{status_text}</div>
                    </div>
                    """
                st.markdown(html_list, unsafe_allow_html=True)
                
            # Manueller Aktualisieren-Button statt fehleranfälliger Pause
            st.write("---")
            if st.button("🔄 Daten aktualisieren"):
                st.rerun()
                
        else:
            st.error(f"Tourdaten konnten nicht geladen werden. Fehlercode: {response.status_code}")
            
    except Exception as e:
        st.error(f"Fehler bei der Verbindung zum Server: {e}")
