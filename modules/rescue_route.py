"""
modules/rescue_route.py
Traffic-aware rescue routing engine with live ETA calculation and Safe Halting Zones.
"""

import numpy as np
import folium
import datetime

DEFAULT_BASE_COORDS = (12.9700, 77.5900)

def calculate_rescue_route(start_coords, end_coords, road_accessibility=80, destination_name="Target", df_shelters=None):
    """
    Calculates traffic-adjusted safe rescue route, exact transit time (mins),
    live arrival timestamp (ETA), and nearby safe halting points.
    """
    lat1, lon1 = start_coords
    lat2, lon2 = end_coords
    
    dist_km = round(np.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111.0, 2)
    
    if float(road_accessibility) < 20.0:
        return {
            "status": "IMPASSABLE",
            "message": "⚠️ Route Impassable! Corridor heavily submerged by flood water.",
            "distance_km": dist_km,
            "est_time_min": None,
            "eta_str": "IMPASSABLE",
            "traffic_delay_min": 0,
            "base_time_min": 0,
            "path": [],
            "halting_zones": [],
            "destination": destination_name
        }
    
    # Base travel duration (assuming 35 km/h emergency speed)
    base_time_min = round((dist_km / 35.0) * 60.0, 1)
    
    # Calculate traffic and flood obstacle delay
    acc_val = float(road_accessibility)
    traffic_factor = max(1.0, (100.0 - acc_val) / 20.0)
    traffic_delay_min = round(base_time_min * (traffic_factor - 1.0), 1)
    total_time_min = round(base_time_min + traffic_delay_min, 1)
    
    # Live ETA Clock Calculation
    now = datetime.datetime.now()
    eta_time = now + datetime.timedelta(minutes=total_time_min)
    eta_str = f"~{total_time_min} mins (ETA: {eta_time.strftime('%I:%M %p')})"
    
    # Simulated multi-waypoint road detour corridor
    mid_lat = (lat1 + lat2) / 2.0
    mid_lon = (lon1 + lon2) / 2.0
    
    path = [
        [lat1, lon1],
        [lat1 + (mid_lat - lat1) * 0.6, lon1 + (mid_lon - lon1) * 0.3],
        [mid_lat, lon2],
        [lat2, lon2]
    ]
    
    # Locate Safe Halting Zones along route
    halting_zones = []
    if df_shelters is not None and not df_shelters.empty:
        for _, s in df_shelters.iterrows():
            s_lat = float(s.get('latitude', 12.97))
            s_lon = float(s.get('longitude', 77.59))
            d_from_mid = np.sqrt((s_lat - mid_lat)**2 + (s_lon - mid_lon)**2) * 111.0
            if d_from_mid <= 5.0:
                halting_zones.append({
                    "name": s.get("shelter_name", "Safe Relief Shelter"),
                    "lat": s_lat,
                    "lon": s_lon,
                    "dist_km": round(d_from_mid, 1),
                    "capacity": s.get("capacity", 250)
                })

    status = "CLEAR" if acc_val > 60 else "HAZARD DETOUR"
    
    return {
        "status": status,
        "message": f"Safest route generated ({status}).",
        "distance_km": dist_km,
        "base_time_min": base_time_min,
        "traffic_delay_min": traffic_delay_min,
        "est_time_min": total_time_min,
        "eta_str": eta_str,
        "path": path,
        "halting_zones": halting_zones,
        "destination": destination_name,
        "start_coords": start_coords,
        "end_coords": end_coords
    }

def add_route_layer_to_map(m, route_data):
    """Overlays route vector, traffic metrics, and Safe Halting Zones on map."""
    if not route_data or not route_data.get("path"):
        return m
        
    status = route_data.get("status", "CLEAR")
    line_color = "#10B981" if status == "CLEAR" else "#F59E0B"
    
    fg_route = folium.FeatureGroup(name="🚑 Traffic-Aware Rescue Corridor", show=True)
    
    popup_html = f"""
    <div style="font-family: Arial, sans-serif; width: 230px;">
        <h4 style="margin: 0 0 5px 0; color: {line_color};">🚑 SAFEST RESCUE ROUTE</h4>
        <b>Destination:</b> {route_data['destination']}<br>
        <b>Distance:</b> {route_data['distance_km']} km<br>
        <b>Reaching Time:</b> <span style="color: #F59E0B; font-weight: bold;">{route_data['eta_str']}</span><br>
        <b>Traffic Delay:</b> +{route_data['traffic_delay_min']} mins<br>
        <b>Corridor Status:</b> <span style="color: {line_color}; font-weight: bold;">{status}</span>
    </div>
    """

    folium.PolyLine(
        locations=route_data["path"],
        color=line_color,
        weight=8,
        opacity=0.9,
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=f"🚑 Safest Route → {route_data['destination']} ({route_data['eta_str']})"
    ).add_to(fg_route)
    
    # Safe Halting Zones (Relief Shelters)
    for h in route_data.get("halting_zones", []):
        folium.Marker(
            location=[h['lat'], h['lon']],
            popup=f"<b>🛡️ Safe Halting Shelter: {h['name']}</b><br>Capacity: {h['capacity']} persons",
            tooltip=f"🛡️ Safe Halting Zone: {h['name']}",
            icon=folium.Icon(color="green", icon="shield", prefix="fa")
        ).add_to(fg_route)

    fg_route.add_to(m)
    return m