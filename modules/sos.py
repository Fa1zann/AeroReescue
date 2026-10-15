"""
modules/sos.py
Handles SOS emergency alert triggers, session state tracking, and map overlay generation.
"""

import streamlit as st
import datetime
import folium

def init_sos_state():
    """Initializes persistent session state for SOS alerts."""
    if "sos_requests" not in st.session_state:
        st.session_state["sos_requests"] = []
    if "sos_count" not in st.session_state:
        st.session_state["sos_count"] = 0

def render_sos_widget():
    """Renders the SOS Trigger button, confirmation dialog, and active requests table."""
    init_sos_state()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🆘 SOS Emergency Dispatch")
    st.sidebar.caption("⚠️ *Prototype Notice: Records internal emergency request for demo. Does NOT notify real emergency services (NDRF/Police).*")
    
    if st.sidebar.button("🆘 TRIGGER SOS EMERGENCY", type="primary", use_container_width=True):
        st.session_state["show_sos_form"] = True

    if st.session_state.get("show_sos_form", False):
        with st.sidebar.expander("📝 Confirm Emergency Details", expanded=True):
            category = st.selectbox(
                "Emergency Category",
                ["Flood Water Rising", "Trapped Civilian(s)", "Medical Emergency", "Structural Hazard", "Other"]
            )
            locality = st.selectbox(
                "Target Locality",
                ["Hebbal", "Kuvempunagar", "Vijayanagar", "Saraswathipuram", "Nazarbad"]
            )
            message = st.text_input("Details / Message", value="Immediate rescue assistance requested.")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Send SOS", use_container_width=True):
                    st.session_state["sos_count"] += 1
                    sos_id = f"SOS-{st.session_state['sos_count']:03d}"
                    
                    # Map localities to coordinates
                    coords_map = {
                        "Kuvempunagar": (12.9716, 77.5946),
                        "Vijayanagar": (12.9800, 77.6000),
                        "Hebbal": (12.9650, 77.6100),
                        "Saraswathipuram": (12.9550, 77.5700),
                        "Nazarbad": (12.9400, 77.5850)
                    }
                    lat, lon = coords_map.get(locality, (12.9650, 77.6100))
                    
                    new_sos = {
                        "id": sos_id,
                        "locality": locality,
                        "category": category,
                        "message": message,
                        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                        "status": "ACTIVE",
                        "priority": "CRITICAL",
                        "lat": lat,
                        "lon": lon
                    }
                    st.session_state["sos_requests"].append(new_sos)
                    st.session_state["show_sos_form"] = False
                    st.sidebar.success(f"Emergency Alert {sos_id} Active!")
                    st.rerun()
            with c2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state["show_sos_form"] = False
                    st.rerun()

    return st.session_state["sos_requests"]

def add_sos_layer_to_map(m, sos_requests):
    """Overlays active SOS emergency markers onto the Folium map."""
    if not sos_requests:
        return m
        
    fg_sos = folium.FeatureGroup(name="🆘 Active SOS Requests", show=True)
    for req in sos_requests:
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 220px;">
            <h4 style="margin: 0 0 5px 0; color: #dc3545;">🆘 {req['id']} ({req['category']})</h4>
            <b>Locality:</b> {req['locality']}<br>
            <b>Time:</b> {req['timestamp']}<br>
            <b>Priority:</b> <span style="color: red; font-weight: bold;">{req['priority']}</span><hr style="margin: 5px 0;">
            <b>Details:</b> {req['message']}
        </div>
        """
        folium.Marker(
            location=[req['lat'], req['lon']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"🆘 {req['id']} - {req['locality']} ({req['category']})",
            icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa")
        ).add_to(fg_sos)
        
    fg_sos.add_to(m)
    return m