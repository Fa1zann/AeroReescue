"""
modules/animal_rescue.py
Animal Emergency Dispatch & Location Reporting System.
"""

import streamlit as st
import datetime
import folium

def init_animal_state():
    if "animal_alerts" not in st.session_state:
        st.session_state["animal_alerts"] = []

def render_animal_rescue_widget():
    """Renders Animal Distress Reporting interface."""
    init_animal_state()
    st.sidebar.markdown("---")
    st.sidebar.subheader("🐾 Animal Emergency Dispatch")
    st.sidebar.caption("Report trapped animals (Cows, Dogs, Cats, Horses, Livestock) for specialized rescue dispatch.")
    
    with st.sidebar.expander("🐾 Report Animal in Distress", expanded=False):
        species = st.selectbox("Animal Species", ["Cow 🐮", "Dog 🐶", "Cat 🐱", "Horse 🐴", "Livestock 🚜", "Wildlife 🦊"])
        locality = st.selectbox("Locality", ["Hebbal", "Kuvempunagar", "Vijayanagar", "Saraswathipuram", "Nazarbad"], key="animal_loc")
        count = st.number_input("Count / Group Size", min_value=1, max_value=50, value=1)
        condition = st.selectbox("Condition", ["Stranded / Trapped", "Submerged Water", "Injured", "Needs Evacuation"])
        notes = st.text_input("Details / Landmark", value="Trapped on elevated boundary structure.")
        
        if st.button("🚨 Dispatch Animal Rescue"):
            coords_map = {
                "Kuvempunagar": (12.9716, 77.5946),
                "Vijayanagar": (12.9800, 77.6000),
                "Hebbal": (12.9650, 77.6100),
                "Saraswathipuram": (12.9550, 77.5700),
                "Nazarbad": (12.9400, 77.5850)
            }
            lat, lon = coords_map.get(locality, (12.9650, 77.6100))
            
            alert = {
                "id": f"ANIM-{len(st.session_state['animal_alerts'])+1:03d}",
                "species": species,
                "locality": locality,
                "count": count,
                "condition": condition,
                "notes": notes,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                "lat": lat + 0.0015,  # Slight offset so markers don't overlap zone centers
                "lon": lon + 0.0015
            }
            st.session_state["animal_alerts"].append(alert)
            st.sidebar.success(f"Animal Rescue Alert {alert['id']} Logged!")
            st.rerun()

    return st.session_state["animal_alerts"]

def add_animal_layer_to_map(m, animal_alerts):
    """Overlays animal emergency markers onto the map."""
    if not animal_alerts:
        return m
        
    fg_anim = folium.FeatureGroup(name="🐾 Animal Rescue Alerts", show=True)
    for a in animal_alerts:
        icon_symbol = "paw"
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 210px;">
            <h4 style="margin:0 0 4px 0; color: #d97706;">🐾 {a['id']} ({a['species']})</h4>
            <b>Count:</b> {a['count']}<br>
            <b>Locality:</b> {a['locality']}<br>
            <b>Condition:</b> <span style="color: red; font-weight: bold;">{a['condition']}</span><br>
            <b>Details:</b> {a['notes']}
        </div>
        """
        folium.Marker(
            location=[a['lat'], a['lon']],
            popup=folium.Popup(popup_html, max_width=230),
            tooltip=f"🐾 {a['species']} ({a['condition']})",
            icon=folium.Icon(color="orange", icon=icon_symbol, prefix="fa")
        ).add_to(fg_anim)
        
    fg_anim.add_to(m)
    return m