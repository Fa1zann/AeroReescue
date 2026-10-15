"""
modules/gis.py
Interactive Folium GIS Map rendering Esri Hybrid Satellite view (with street & place labels),
permanent locality text badges, and tactical overlays.
"""

import folium
from folium.plugins import MarkerCluster
import pandas as pd

def load_zone_data():
    return pd.read_csv("data/zones.csv")

def load_infrastructure_data():
    df_hospitals = pd.read_csv("data/hospitals.csv") if pd.io.common.file_exists("data/hospitals.csv") else pd.DataFrame()
    df_shelters = pd.read_csv("data/shelters.csv") if pd.io.common.file_exists("data/shelters.csv") else pd.DataFrame()
    return df_hospitals, df_shelters

def build_disaster_map(df_risk, df_hospitals=None, df_shelters=None, rescuer_location=None, sos_requests=None, active_route=None, animal_alerts=None, victim_detections=None):
    center_lat = df_risk['latitude'].mean() if not df_risk.empty else 12.9716
    center_lon = df_risk['longitude'].mean() if not df_risk.empty else 77.5946
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles=None)
    
    # Base Layer 1: OpenStreetMap
    folium.TileLayer('openstreetmap', name='🗺️ Standard Map').add_to(m)
    
    # Base Layer 2: Esri World Imagery (Satellite)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='🛰️ Esri Satellite Base',
        overlay=False,
        control=True
    ).add_to(m)

    # Reference Overlay: Esri World Boundaries & Places (Adds Street Names & City Labels)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Boundaries & Places',
        name='🏷️ Place & Street Labels',
        overlay=True,
        control=True,
        show=True
    ).add_to(m)
    
    # Layer 1: Flood Risk Sectors + Permanent Locality Text Labels
    fg_risk = folium.FeatureGroup(name="⚠️ Flood Risk Sectors & Labels", show=True)
    for _, row in df_risk.iterrows():
        score = row.get('risk_score', 50)
        color = "#EF4444" if score >= 75 else "#F59E0B" if score >= 55 else "#10B981"
        zone_name = row.get('zone_name', 'Sector')
        
        # 1A. Risk Sector Circle Marker
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=16 + (score / 7.0),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.45,
            popup=f"<b>{zone_name}</b><br>Risk Score: {score}/100<br>Severity: {row.get('flood_severity', 50)}%",
            tooltip=f"📍 {zone_name} ({score}/100)"
        ).add_to(fg_risk)

        # 1B. PERMANENT TEXT BADGE (Stamps locality name directly onto satellite view)
        html_label = f"""
        <div style="
            font-family: 'Outfit', Arial, sans-serif;
            font-size: 11px;
            font-weight: 800;
            color: #FFFFFF;
            background: rgba(11, 14, 20, 0.85);
            border: 1px solid {color};
            border-radius: 4px;
            padding: 2px 6px;
            white-space: nowrap;
            box-shadow: 0 2px 6px rgba(0,0,0,0.6);
            transform: translate(-50%, -28px);
            text-align: center;
        ">
            📍 {zone_name.upper()}
        </div>
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            icon=folium.DivIcon(html=html_label)
        ).add_to(fg_risk)

    fg_risk.add_to(m)
    
    # Layer 2: Live Rescuer Location
    if rescuer_location and rescuer_location.get("location"):
        loc = rescuer_location["location"]
        folium.Marker(
            location=[loc['lat'], loc['lon']],
            popup=f"<b>📍 LIVE RESCUER GPS</b><br>Lat: {loc['lat']}<br>Lon: {loc['lon']}",
            tooltip="📍 LIVE RESCUER GPS POSITION",
            icon=folium.Icon(color="darkpurple", icon="user", prefix="fa")
        ).add_to(m)
        
    # Layer 3: Active SOS Requests
    if sos_requests:
        from modules.sos import add_sos_layer_to_map
        add_sos_layer_to_map(m, sos_requests)

    # Layer 4: Animal Rescue Alerts
    if animal_alerts:
        from modules.animal_rescue import add_animal_layer_to_map
        add_animal_layer_to_map(m, animal_alerts)

    # Layer 5: Traffic-Aware Rescue Corridor
    if active_route and active_route.get("path"):
        from modules.rescue_route import add_route_layer_to_map
        add_route_layer_to_map(m, active_route)

    # Layer 6: AI Victim Detections
    if victim_detections:
        from modules.victim_detection import add_victim_layer_to_map
        add_victim_layer_to_map(m, victim_detections)

    folium.LayerControl(collapsed=False).add_to(m)
    return m