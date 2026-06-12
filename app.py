import streamlit as st
import requests
import time
from datetime import datetime, timedelta # <--- timedelta hinzugefügt

# ... (CSS und Übersetzungen bleiben identisch)

    # In der Schleife für die Checkpoints fügen wir die Korrektur ein:
    for cp in route.get("checkpoints", []):
        an_str = cp.get('realArrivalTime')
        start_str = cp.get('deliverSince')
        ende_str = cp.get('deliverTill')
        
        status_text = t["Offen"]
        color = "gray"
        ist_time = "--:--"
        
        if an_str and start_str and ende_str:
            try:
                # 1. Strings in UTC-Zeitobjekte umwandeln
                an = datetime.fromisoformat(an_str.replace("Z", "+00:00"))
                start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                ende = datetime.fromisoformat(ende_str.replace("Z", "+00:00"))
                
                # 2. HIER DIE KORREKTUR: + 2 Stunden
                korrektur = timedelta(hours=2)
                an += korrektur
                start += korrektur
                ende += korrektur
                
                # Anzeigenzeit formatieren
                ist_time = an.strftime("%H:%M")
                
                # 3. Vergleich mit korrigierten Werten
                if an < start:
                    diff = int((start - an).total_seconds() / 60)
                    status_text = f"{diff} {t['Früh']}"
                    color = "#0056b3"
                elif an > ende:
                    diff = int((an - ende).total_seconds() / 60)
                    status_text = f"{diff} {t['Spät']}"
                    color = "#dc3545"
                else:
                    status_text = t["Pünktlich"]
                    color = "#28a745"
            except Exception:
                pass
        
        # HTML mit den korrigierten Werten
        html_list += f"""
        <div class="stop-card" style="border-left: 5px solid {color};">
            <div class="stop-info">
                <div class="stop-address">{cp.get('address')}</div>
                <div class="stop-times">{t['Fenster']}: {start.strftime("%H:%M")}-{ende.strftime("%H:%M")} | {t['Ist']}: <b>{ist_time}</b></div>
            </div>
            <div class="stop-status" style="color: {color};">{status_text}</div>
        </div>
        """
