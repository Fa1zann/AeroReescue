"""
app.py - OVERWATCH2 Command Center
Two-Color Tactical Platform with 3D Physics Buttons, Reaching Time Calculation,
Esri Satellite View, Animal Rescue Dispatch, and Victim Verification Engine.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from streamlit_folium import st_folium

from modules.gis import load_zone_data, load_infrastructure_data, build_disaster_map
from modules.risk_engine import calculate_zone_risk
from modules.weather import get_zone_weather
from modules.vision import analyze_aerial_image
from modules.location import render_location_widget, generate_localized_zones
from modules.sos import render_sos_widget
from modules.rescue_route import calculate_rescue_route, DEFAULT_BASE_COORDS
from modules.flood_forecast import predict_multi_horizon_risk, create_forecast_trajectory_chart
from modules.search_priority import calculate_search_priorities
from modules.voice_navigation import render_voice_controller
from modules.theme import inject_command_center_theme, apply_plotly_command_center_theme
from modules.animal_rescue import render_animal_rescue_widget
from modules.radar_chart import create_sector_radar_chart
from modules.victim_detection import analyze_victim_imagery, init_victim_state

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & THEME
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="OVERWATCH2 — Tactical Disaster Intelligence",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_command_center_theme()

if "zone_overrides" not in st.session_state:
    st.session_state["zone_overrides"] = {}

# -----------------------------------------------------------------------------
# 2. SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
st.sidebar.title("🚨 OVERWATCH2")
st.sidebar.caption("Tactical Disaster Command Platform")

st.sidebar.markdown("---")
st.sidebar.subheader("🕹️ Mission Parameters")

disaster_type = st.sidebar.selectbox("Disaster Type", ["Flood Emergency", "Flash Inundation"], index=0)
operation_mode = st.sidebar.radio("Execution Mode", ["Demo Mode (Offline Safe)", "Live API Mode"])

st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Risk Weight Tuner")
w_flood = st.sidebar.slider("Flood Extent Weight", 0.0, 0.6, 0.35, 0.05)
w_pop = st.sidebar.slider("Population Weight", 0.0, 0.5, 0.25, 0.05)
w_weather = st.sidebar.slider("Weather Weight", 0.0, 0.4, 0.15, 0.05)
w_access = st.sidebar.slider("Inaccessibility Weight", 0.0, 0.4, 0.15, 0.05)
w_infra = st.sidebar.slider("Infrastructure Weight", 0.0, 0.3, 0.10, 0.05)

custom_weights = {
    'flood': w_flood, 'population': w_pop, 'weather': w_weather,
    'accessibility': w_access, 'infrastructure': w_infra
}

# Sidebar Tactical Modules
rescuer_loc = render_location_widget()
sos_requests = render_sos_widget()
animal_alerts = render_animal_rescue_widget()
init_victim_state()
render_voice_controller()

# -----------------------------------------------------------------------------
# 3. DATA FUSION ENGINE & DYNAMIC SECTOR INITIALIZATION
# -----------------------------------------------------------------------------
def fuse_disaster_telemetry(lat, lon):
    """
    Data Fusion Core: Fuses live GPS position, OpenStreetMap spatial data,
    meteorological metrics, population exposure, and infrastructure vulnerability
    into a unified tactical data frame.
    """
    df_fused_risk, df_fused_forecast = generate_localized_zones(lat, lon)
    
    # Apply Operator Overrides (Drone Vision & Manual Inputs)
    if "zone_overrides" in st.session_state:
        for z_id, override_sev in st.session_state["zone_overrides"].items():
            if z_id in df_fused_risk['zone_id'].values:
                idx = df_fused_risk[df_fused_risk['zone_id'] == z_id].index[0]
                df_fused_risk.at[idx, 'flood_severity'] = override_sev
                
                # Re-calculate fused score with updated CV severity
                pop_dens = df_fused_risk.at[idx, 'population_density']
                rain_mm = df_fused_risk.at[idx, 'weather_rain_mm']
                road_acc = df_fused_risk.at[idx, 'road_accessibility']
                
                new_score = int(min(99, max(15, override_sev * 0.45 + (pop_dens / 250) * 0.35 + (rain_mm / 1.5) * 0.2)))
                df_fused_risk.at[idx, 'risk_score'] = new_score
                df_fused_risk.at[idx, 'risk_category'] = "CRITICAL" if new_score >= 75 else "HIGH" if new_score >= 55 else "MODERATE"

    return df_fused_risk, df_fused_forecast

# Load static infrastructure assets (Hospitals & Shelters)
df_hospitals, df_shelters = load_infrastructure_data()

# Trigger Data Fusion around Active GPS Position
if "active_df_risk" not in st.session_state:
    init_lat = 13.0125
    init_lon = 77.7040
    if "rescuer_location" in st.session_state and st.session_state["rescuer_location"].get("location"):
        init_lat = st.session_state["rescuer_location"]["location"]["lat"]
        init_lon = st.session_state["rescuer_location"]["location"]["lon"]
        
    df_risk_fused, df_forecast_fused = fuse_disaster_telemetry(init_lat, init_lon)
    st.session_state["active_df_risk"] = df_risk_fused
    st.session_state["active_df_forecast"] = df_forecast_fused

# Bind fused data frames to active session
df_risk = st.session_state["active_df_risk"]
df_forecast = st.session_state["active_df_forecast"]

# Status flag for UI views
data_loaded = not df_risk.empty

# -----------------------------------------------------------------------------
# 4. BRAND HEADER & AUTOMATED ALARM BANNER
# -----------------------------------------------------------------------------
st.markdown(f"""
<div class="brand-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin:0; font-size: 1.8rem; font-weight: 800; color: #F9FAFB;">
                🚨 OVERWATCH2 <span style="color: #F59E0B; font-size: 1.1rem; font-weight: 600;">| Tactical Disaster Intelligence</span>
            </h1>
            <p style="margin: 4px 0 0 0; color: #9CA3AF; font-size: 0.85rem;">
                <b>Scenario:</b> <span style="color: #10B981;">{disaster_type}</span> &nbsp;|&nbsp; 
                <b>Mode:</b> <span style="color: #F59E0B;">{operation_mode}</span> &nbsp;|&nbsp; 
                <span style="color: #F59E0B;">⚠️ Simulated Flood Scenario for Prototype Demonstration</span>
            </p>
        </div>
        <div>
            <span style="background-color: #161C28; border: 1px solid #2D3748; color: #10B981; padding: 6px 14px; border-radius: 20px; font-size: 0.78rem; font-weight: 700;">
                🟢 SENSORS ACTIVE
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if data_loaded:
    max_flood = df_risk['flood_severity'].max()
    critical_locs = df_risk[df_risk['flood_severity'] >= 80]['zone_name'].tolist()
    
    if max_flood >= 80 or critical_locs:
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #7F1D1D 0%, #B91C1C 100%); border: 1px solid #EF4444; color: white; padding: 12px 18px; border-radius: 8px; font-weight: 700; margin-bottom: 16px;">
            🚨 <b>AUTOMATED EMERGENCY ALARM TRIGGERED:</b> Severe Flood Surge Detected in <b>{", ".join(critical_locs)}</b> (Peak Severity: {max_flood}%)
        </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. TOP METRICS
# -----------------------------------------------------------------------------
if data_loaded:
    df_forecast = predict_multi_horizon_risk(df_risk)
    df_search = calculate_search_priorities(df_risk, df_forecast, sos_requests)
    top_target = df_search.iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    critical_count = len(df_risk[df_risk['risk_category'] == 'CRITICAL'])
    unverified_victims = len([v for v in st.session_state.get('victim_detections', []) if v.get('status') == 'UNVERIFIED'])

    c1.metric("Monitored Sectors", f"{len(df_risk)} Localities")
    c2.metric("CRITICAL Threat Sectors", f"{critical_count} Localities", delta="Immediate Action", delta_color="inverse")
    c3.metric("Top Dispatch Target", top_target['zone_name'], delta=f"Priority: {top_target['search_priority']}/100")
    c4.metric("AI Victim Detections", f"{len(st.session_state.get('victim_detections', []))} Detected", delta=f"{unverified_victims} Unverified", delta_color="inverse")

    st.info(f"🚁 **NEXT SEARCH & RESCUE TARGET:** **{top_target['zone_name']}** (Priority Index: `{top_target['search_priority']} / 100`) — *Key Factors: {top_target['reasons']}*")

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. NATIVE COMMAND BAR DISPATCHER
# -----------------------------------------------------------------------------
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "GIS Map"

def set_active_page(page_name):
    st.session_state["active_page"] = page_name

current_page = st.session_state["active_page"]

# Top Tactical Command Bar
c_tb1, c_tb2, c_tb3, c_tb4, c_tb5 = st.columns(5)

with c_tb1:
    st.button(
        "🗺️ GIS Map",
        type="primary" if current_page == "GIS Map" else "secondary",
        on_click=set_active_page, args=("GIS Map",),
        use_container_width=True
    )

with c_tb2:
    st.button(
        "🔮 Prediction",
        type="primary" if current_page == "Prediction" else "secondary",
        on_click=set_active_page, args=("Prediction",),
        use_container_width=True
    )

with c_tb3:
    st.button(
        "📸 Drone Vision",
        type="primary" if current_page == "Vision" else "secondary",
        on_click=set_active_page, args=("Vision",),
        use_container_width=True
    )

with c_tb4:
    st.button(
        "🔎 Risk Radar",
        type="primary" if current_page == "Radar" else "secondary",
        on_click=set_active_page, args=("Radar",),
        use_container_width=True
    )

with c_tb5:
    st.button(
        "📊 Field Data",
        type="primary" if current_page == "Data" else "secondary",
        on_click=set_active_page, args=("Data",),
        use_container_width=True
    )

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. TAB CONTENT DISPATCH
# -----------------------------------------------------------------------------

# PAGE 1: GIS MAP
if current_page == "GIS Map":
    st.subheader("Interactive Tactical GIS Map (Esri Satellite & Vector Controls)")
    if data_loaded:
        forecast_horizon = st.radio(
            "🔮 **GIS Map Forecast Horizon Controls:**",
            ["Current", "+1 Hour", "+3 Hours", "+6 Hours"],
            horizontal=True
        )
        
        df_map_projected = df_risk.copy()
        horizon_cols = {
            "Current": ("current_score", "current_cat"),
            "+1 Hour": ("score_1h", "cat_1h"),
            "+3 Hours": ("score_3h", "cat_3h"),
            "+6 Hours": ("score_6h", "cat_6h")
        }
        score_col, cat_col = horizon_cols[forecast_horizon]
        
        for idx, row in df_map_projected.iterrows():
            f_row = df_forecast[df_forecast['zone_id'] == row['zone_id']].iloc[0]
            df_map_projected.at[idx, 'risk_score'] = f_row[score_col]
            df_map_projected.at[idx, 'risk_category'] = f_row[cat_col]

        st.markdown("---")
        st.markdown("#### 🚑 Safest Rescue Route & Live Reaching Time Calculator")
        c_r1, c_r2 = st.columns([2, 1])
        
        with c_r1:
            loc_list = df_map_projected['zone_name'].tolist()
            default_idx = 0
            voice_loc = st.session_state.get("selected_locality_voice")
            if voice_loc and voice_loc in loc_list:
                default_idx = loc_list.index(voice_loc)
                
            route_target = st.selectbox("Select Target Locality for Rescue Dispatch:", loc_list, index=default_idx)
        
        target_row = df_map_projected[df_map_projected['zone_name'] == route_target].iloc[0]
        
        start_pt = DEFAULT_BASE_COORDS
        if rescuer_loc and rescuer_loc.get("location"):
            start_pt = (rescuer_loc["location"]["lat"], rescuer_loc["location"]["lon"])
            
        end_pt = (target_row['latitude'], target_row['longitude'])
        road_acc = target_row.get('road_accessibility', 80)
        
        active_route = calculate_rescue_route(
            start_pt, end_pt, road_accessibility=road_acc, destination_name=route_target, df_shelters=df_shelters
        )
        
        with c_r2:
            if active_route["status"] == "IMPASSABLE":
                st.error(active_route["message"])
            else:
                st.success(f"⏱️ **REACHING TIME:** **{active_route['eta_str']}**")
                st.caption(f"**Distance:** `{active_route['distance_km']} km` | **Traffic Delay:** `+{active_route['traffic_delay_min']} mins` | **Halting Zones:** `{len(active_route['halting_zones'])} Shelters`")

        folium_map = build_disaster_map(
            df_map_projected, df_hospitals, df_shelters, rescuer_location=rescuer_loc,
            sos_requests=sos_requests, active_route=active_route, animal_alerts=animal_alerts,
            victim_detections=st.session_state.get('victim_detections', [])
        )
        st_folium(folium_map, width="100%", height=520)

# PAGE 2: PREDICTIVE ESCALATION
elif current_page == "Prediction":
    st.subheader("🔮 Multi-Horizon Flood Risk Forecasting (+1h, +3h, +6h)")
    if data_loaded:
        fig_forecast = create_forecast_trajectory_chart(df_forecast)
        fig_forecast = apply_plotly_command_center_theme(fig_forecast)
        st.plotly_chart(fig_forecast, use_container_width=True)

# PAGE 3: AERIAL DRONE VISION ENGINE
elif current_page == "Vision":
    st.subheader("📸 Aerial Drone Vision Workspace")
    
    c_u1, c_u2, c_u3 = st.columns([2, 1, 1])
    with c_u1:
        uploaded_file = st.file_uploader("Upload Drone Photo", type=["jpg", "jpeg", "png"])
    with c_u2:
        sensitivity_level = st.slider("🔍 SAR Anomaly Sensitivity:", 20.0, 100.0, 70.0, 5.0, help="Slide left to ignore debris. Slide right to find faint targets.")
    with c_u3:
        target_size = st.slider("📏 Target Person Size (px):", 10, 80, 20, 5, help="Match this to how large humans appear in the photo (Drone Altitude).")

    img_bytes = None
    if uploaded_file is not None:
        img_bytes = uploaded_file.read()
    elif os.path.exists("assets/sample_drone_flood.jpg"):
        with open("assets/sample_drone_flood.jpg", "rb") as f:
            img_bytes = f.read()

    if img_bytes is not None:
        try:
            target_zone_name = st.selectbox("Select Target Sector for Drone Analysis:", df_risk['zone_name'])
            target_row = df_risk[df_risk['zone_name'] == target_zone_name].iloc[0]

            res_flood = analyze_aerial_image(img_bytes)
            res_victim = analyze_victim_imagery(
                img_bytes, target_row['latitude'], target_row['longitude'], target_zone_name, 
                sensitivity=sensitivity_level, target_size=target_size
            )

            col_v1, col_v2 = st.columns(2)
            with col_v1:
                st.image(res_flood['processed_image'], caption="1. Original Image + Translucent Water Map", use_container_width=True)
                st.info(f"**Terrain:** `{res_flood['water_surface_type']}` | **Water Coverage:** `{res_flood['flood_percentage']}%` | **Severity:** `{res_flood['calculated_severity']}/100`")
                
            with col_v2:
                st.image(res_victim['annotated_image'], caption="2. AI Victim Detection Overlay", use_container_width=True)
                st.warning(f"🆘 **Estimated Victims Detected:** `{res_victim['victim_count']} Person(s)` (⚠️ UNVERIFIED)")

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                if st.button("🚀 Fuse Inundation Findings to GIS Map", type="primary", use_container_width=True):
                    target_zone_id = df_risk[df_risk['zone_name'] == target_zone_name]['zone_id'].values[0]
                    st.session_state["zone_overrides"][target_zone_id] = res_flood['calculated_severity']
                    st.success("Flood severity updated!")
                    st.rerun()

            with col_f2:
                if st.button("🆘 Log AI Victim Detections to Map (Unverified)", use_container_width=True):
                    st.session_state["victim_detections"].extend(res_victim["detections"])
                    st.sidebar.success(f"{res_victim['victim_count']} Victim Detections Logged!")
                    st.rerun()

            if st.session_state.get("victim_detections"):
                st.markdown("---")
                st.subheader("📋 Ground Verification Control Matrix")

                to_delete = None
                for idx, v in enumerate(st.session_state["victim_detections"]):
                    c_v1, c_v2, c_v3, c_v4 = st.columns([2, 2, 2, 3])
                    c_v1.write(f"**ID:** `{v['id']}`")
                    c_v2.write(f"**Sector:** {v['sector']} ({v['confidence']}%)")
                    c_v3.write(f"**Status:** `{v['status']}`")
                    with c_v4:
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            if v['status'] == "UNVERIFIED":
                                if st.button(f"✅ Confirm", key=f"verify_{idx}"):
                                    st.session_state["victim_detections"][idx]["status"] = "VERIFIED"
                                    st.rerun()
                            else:
                                st.success("VERIFIED")
                        with col_b2:
                            if st.button(f"❌ Remove", key=f"del_{idx}"):
                                to_delete = idx

                if to_delete is not None:
                    st.session_state["victim_detections"].pop(to_delete)
                    st.rerun()
        except Exception as e:
            st.error(f"Error executing computer vision pipeline: {e}")

# PAGE 4: EXPLAINABLE RISK & RADAR
elif current_page == "Radar":
    st.subheader("🔎 Explainable Risk Factor Audit & Radar Chart")
    if data_loaded:
        selected_zone_name = st.selectbox("Select Target Locality for Radar Audit:", df_risk['zone_name'], key="explain_select")
        
        c_rad1, c_rad2 = st.columns(2)
        with c_rad1:
            fig_radar = create_sector_radar_chart(df_risk, selected_zone_name)
            st.plotly_chart(fig_radar, use_container_width=True)
            
        with c_rad2:
            zone_data = df_risk[df_risk['zone_name'] == selected_zone_name].iloc[0]
            bd = zone_data['breakdown']
            chart_df = pd.DataFrame({'Risk Factor': list(bd.keys()), 'Points Contributed': list(bd.values())})
            fig = px.bar(
                chart_df, x='Points Contributed', y='Risk Factor', orientation='h',
                title=f"Factor Contributions for {zone_data['zone_name']}",
                color='Points Contributed', color_continuous_scale='Reds', text='Points Contributed'
            )
            fig = apply_plotly_command_center_theme(fig)
            fig.update_layout(height=320, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

# PAGE 5: FIELD DATA
elif current_page == "Data":
    st.subheader("Field Metrics & Data Fusion Table")
    if data_loaded:
        st.dataframe(
            df_risk[['zone_id', 'zone_name', 'risk_score', 'risk_category', 'flood_severity', 'weather_rain_mm', 'road_accessibility']], 
            use_container_width=True
        )