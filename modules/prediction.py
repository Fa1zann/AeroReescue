"""
app.py - AeroRescue AI Command Center
Full Dashboard featuring Predictive Risk Escalation & Evacuation Network Optimization.
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
from modules.predictive import predict_zone_escalation, calculate_shortest_evacuation_route

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AeroRescue AI — Disaster Response",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "zone_overrides" not in st.session_state:
    st.session_state["zone_overrides"] = {}

# -----------------------------------------------------------------------------
# 2. SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
st.sidebar.title("🛸 AeroRescue AI")
st.sidebar.caption("Predictive Disaster Response Platform")

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

# -----------------------------------------------------------------------------
# 3. DATA FUSION & PREDICTIVE PROCESSING
# -----------------------------------------------------------------------------
st.title("🛸 AeroRescue AI — Command Center")
st.markdown(f"**Active Scenario:** `{disaster_type}` | **Execution Mode:** `{operation_mode}`")
st.markdown("---")

try:
    df_zones = load_zone_data()
    df_hospitals, df_shelters = load_infrastructure_data()
    
    processed_zones = []
    weather_sources = set()

    for idx, row in df_zones.iterrows():
        zone_id = row['zone_id']
        current_flood_sev = st.session_state["zone_overrides"].get(zone_id, row['flood_severity'])

        w_data = get_zone_weather(row['latitude'], row['longitude'], zone_id=zone_id)
        weather_sources.add(w_data['source'])

        risk_res = calculate_zone_risk(
            current_flood_sev, row['population_exposure'], w_data['weather_risk'],
            row['road_accessibility'], row['infrastructure_exposure'], weights=custom_weights
        )
        
        processed_zones.append({
            **row.to_dict(),
            'flood_severity': current_flood_sev,
            'weather_temp': w_data['temperature'],
            'weather_rain_mm': w_data['rainfall_mm'],
            'weather_risk': w_data['weather_risk'],
            'weather_desc': w_data['description'],
            'weather_source': w_data['source'],
            'risk_score': risk_res['total_score'],
            'risk_category': risk_res['category'],
            'breakdown': risk_res['breakdown']
        })
        
    df_risk = pd.DataFrame(processed_zones)
    
    # Run Predictive Escalation Model
    df_pred = predict_zone_escalation(df_risk)
    data_loaded = True
except Exception as e:
    st.error(f"Error processing data fusion: {e}")
    data_loaded = False

# -----------------------------------------------------------------------------
# 4. TOP METRICS
# -----------------------------------------------------------------------------
if data_loaded:
    c1, c2, c3, c4 = st.columns(4)
    critical_count = len(df_pred[df_pred['risk_category'] == 'CRITICAL'])
    top_priority_zone = df_pred.iloc[0]['zone_name']

    c1.metric("Monitored Zones", f"{len(df_pred)} Sectors")
    c2.metric("CRITICAL Threat Zones", f"{critical_count} Sectors", delta="Action Required", delta_color="inverse")
    c3.metric("Top Search Priority", top_priority_zone, delta="Rank #1")
    c4.metric("Predictive Engine", "ACTIVE 🔮", delta="3h/6h Horizon")

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. NAVIGATION TABS
# -----------------------------------------------------------------------------
tab_gis, tab_pred, tab_vision, tab_explain = st.tabs([
    "🗺️ GIS Intelligence Map",
    "🔮 Predictive Escalation & Routing",
    "📸 Aerial Drone Analysis",
    "🔎 Explainable Risk Matrix"
])

# TAB 1: GIS MAP
with tab_gis:
    st.subheader("Interactive Situational Map")
    if data_loaded:
        folium_map = build_disaster_map(df_pred, df_hospitals, df_shelters)
        st_folium(folium_map, width="100%", height=520)

# TAB 2: PREDICTIVE ESCALATION & ROUTING
with tab_pred:
    st.subheader("🔮 3h & 6h Flood Risk Forecasts")
    st.write("Model predicts water surge accumulation based on rainfall rate and elevation slopes:")
    
    if data_loaded:
        # Comparison Bar Chart (Current vs 3h vs 6h)
        chart_data = []
        for _, r in df_pred.iterrows():
            chart_data.append({'Zone': r['zone_name'], 'Time Horizon': '1. Current Risk', 'Risk Score': r['risk_score']})
            chart_data.append({'Zone': r['zone_name'], 'Time Horizon': '2. Projected +3h', 'Risk Score': r['predicted_risk_3h']})
            chart_data.append({'Zone': r['zone_name'], 'Time Horizon': '3. Projected +6h', 'Risk Score': r['predicted_risk_6h']})
            
        df_chart = pd.DataFrame(chart_data)
        fig_pred = px.bar(
            df_chart, x='Zone', y='Risk Score', color='Time Horizon', barmode='group',
            title="Risk Index Escalation Trajectory Across Monitored Sectors",
            color_discrete_sequence=['#ffc107', '#fd7e14', '#dc3545']
        )
        fig_pred.update_layout(height=380)
        st.plotly_chart(fig_pred, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🚑 Evacuation Route Optimization (NetworkX)")
        selected_zone_for_route = st.selectbox("Select Target Zone to Calculate Safe Evacuation Route:", df_pred['zone_name'])
        target_z = df_pred[df_pred['zone_name'] == selected_zone_for_route].iloc[0]
        
        routes_df = calculate_shortest_evacuation_route(target_z, df_hospitals, df_shelters)
        
        col_r1, col_r2 = st.columns([1, 2])
        with col_r1:
            st.metric("Origin Zone", target_z['zone_name'])
            st.write(f"- Road Accessibility: `{target_z['road_accessibility']}/100`")
            st.write(f"- Elevation: `{target_z['elevation_m']} m`")
            if target_z['road_accessibility'] < 30:
                st.error("🚨 HIGH HAZARD: Main access corridors heavily submerged!")
            else:
                st.success("🟢 Route corridors accessible for emergency response vehicles.")
                
        with col_r2:
            st.markdown("#### Recommended Evacuation Facilities & Est. Transit Times")
            st.dataframe(routes_df, use_container_width=True)

# TAB 3: AERIAL DRONE ANALYSIS
with tab_vision:
    st.subheader("Aerial Drone Processing")
    uploaded_file = st.file_uploader("Upload Drone Photo", type=["jpg", "jpeg", "png"])
    use_sample = st.button("📁 Load Sample Drone Image")
    
    img_bytes = None
    if uploaded_file is not None:
        img_bytes = uploaded_file.read()
    elif use_sample or os.path.exists("assets/sample_drone_flood.jpg"):
        if os.path.exists("assets/sample_drone_flood.jpg"):
            with open("assets/sample_drone_flood.jpg", "rb") as f:
                img_bytes = f.read()

    if img_bytes is not None:
        try:
            res = analyze_aerial_image(img_bytes)
            c_i1, c_i2 = st.columns(2)
            c_i1.image(img_bytes, caption="Raw Frame", use_container_width=True)
            c_i2.image(res['processed_image'], caption="HSV Mask", use_container_width=True)
            st.success(f"Flood Coverage: {res['flood_percentage']}% | Generated Severity: {res['calculated_severity']}/100")
            
            target_zone_name = st.selectbox("Select Target Sector to Update:", df_pred['zone_name'])
            target_zone_id = df_pred[df_pred['zone_name'] == target_zone_name]['zone_id'].values[0]
            
            if st.button("🚀 Fuse Findings into Live GIS Map", type="primary"):
                st.session_state["zone_overrides"][target_zone_id] = res['calculated_severity']
                st.balloons()
                st.rerun()
        except Exception as e:
            st.error(f"Error executing computer vision pipeline: {e}")

# TAB 4: EXPLAINABLE MATRIX
with tab_explain:
    st.subheader("Factor Breakdown Audit")
    if data_loaded:
        selected_zone_name = st.selectbox("Select Target Zone:", df_pred['zone_name'], key="explain_select")
        zone_data = df_pred[df_pred['zone_name'] == selected_zone_name].iloc[0]
        
        col_m, col_chart = st.columns([1, 2])
        with col_m:
            st.metric("Risk Score", f"{zone_data['risk_score']} / 100", delta=f"Category: {zone_data['risk_category']}")
            st.write(f"- Weather Condition: `{zone_data['weather_desc']}`")
            st.write(f"- 1h Rainfall: `{zone_data['weather_rain_mm']} mm/h`")
            
        with col_chart:
            bd = zone_data['breakdown']
            chart_df = pd.DataFrame({'Risk Factor': list(bd.keys()), 'Points Contributed': list(bd.values())})
            fig = px.bar(
                chart_df, x='Points Contributed', y='Risk Factor', orientation='h',
                title=f"Factor Contributions for {zone_data['zone_name']}",
                color='Points Contributed', color_continuous_scale='Reds', text='Points Contributed'
            )
            fig.update_layout(height=320, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)