"""
modules/radar_chart.py
Radar Chart Generator comparing sector-level risk dimensions against regional averages.
Handles column mapping dynamically to prevent missing key errors.
"""

import plotly.graph_objects as go
import pandas as pd

def create_sector_radar_chart(df_risk, selected_zone_name):
    """
    Generates a polar radar chart comparing a selected sector's risk profile
    against regional baseline averages.
    """
    df = df_risk.copy()
    
    # 1. Dynamic Column Normalization & Compatibility Mapping
    if 'population_exposure' not in df.columns:
        if 'population_density' in df.columns:
            max_pop = df['population_density'].max() if df['population_density'].max() > 0 else 1
            df['population_exposure'] = (df['population_density'] / max_pop) * 100.0
        else:
            df['population_exposure'] = 50.0

    if 'infrastructure_vulnerability' not in df.columns:
        if 'road_accessibility' in df.columns:
            df['infrastructure_vulnerability'] = 100.0 - df['road_accessibility']
        else:
            df['infrastructure_vulnerability'] = 50.0

    if 'weather_rain_mm' not in df.columns:
        df['weather_rain_mm'] = 50.0

    if 'flood_severity' not in df.columns:
        df['flood_severity'] = 50.0

    # 2. Extract Target Sector Row
    zone_data = df[df['zone_name'] == selected_zone_name]
    if zone_data.empty:
        zone_data = df.iloc[0:1]
    
    row = zone_data.iloc[0]
    
    # 3. Compile Metrics for Target Sector
    val_flood = float(row.get('flood_severity', 50))
    val_pop = float(row.get('population_exposure', 50))
    val_rain = float(min(100, row.get('weather_rain_mm', 50)))
    val_infra = float(row.get('infrastructure_vulnerability', 50))
    
    sector_values = [val_flood, val_pop, val_rain, val_infra]
    
    # 4. Compile Regional Average Baselines
    avg_flood = float(df['flood_severity'].mean())
    avg_pop = float(df['population_exposure'].mean())
    avg_rain = float(df['weather_rain_mm'].clip(upper=100).mean())
    avg_infra = float(df['infrastructure_vulnerability'].mean())
    
    avg_values = [avg_flood, avg_pop, avg_rain, avg_infra]
    
    # Categories & Loop Closure
    categories = ['Flood Severity', 'Population Exposure', 'Precipitation Volume', 'Infra Vulnerability']
    categories_closed = categories + [categories[0]]
    sector_values_closed = sector_values + [sector_values[0]]
    avg_values_closed = avg_values + [avg_values[0]]
    
    # 5. Build Plotly Radar Chart
    fig = go.Figure()
    
    # Selected Sector Trace
    fig.add_trace(go.Scatterpolar(
        r=sector_values_closed,
        theta=categories_closed,
        fill='toself',
        name=selected_zone_name,
        line=dict(color='#F59E0B', width=2),
        fillcolor='rgba(245, 158, 11, 0.35)'
    ))
    
    # Regional Baseline Average Trace
    fig.add_trace(go.Scatterpolar(
        r=avg_values_closed,
        theta=categories_closed,
        fill='toself',
        name='Regional Baseline Avg',
        line=dict(color='#6B7280', width=1, dash='dash'),
        fillcolor='rgba(107, 114, 128, 0.15)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="#2D3748",
                tickfont=dict(color="#9CA3AF", size=9)
            ),
            angularaxis=dict(
                gridcolor="#2D3748",
                tickfont=dict(color="#F9FAFB", size=11, family="Outfit")
            ),
            bgcolor="#0B0E14"
        ),
        paper_bgcolor="#161C28",
        plot_bgcolor="#0B0E14",
        showlegend=True,
        legend=dict(
            bgcolor="#11151F",
            bordercolor="#2D3748",
            font=dict(color="#F9FAFB", size=11)
        ),
        title=dict(
            text=f"Tactical Risk Audit: {selected_zone_name}",
            font=dict(color="#F59E0B", size=14, family="Outfit")
        ),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    
    return fig