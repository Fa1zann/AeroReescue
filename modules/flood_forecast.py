"""
modules/flood_forecast.py
Multi-horizon flood risk forecasting engine (+1h, +3h, +6h) based on elevation gradients
and rainfall intensity rates.
"""

import pandas as pd
import plotly.express as px

def get_risk_category(score):
    """Categorizes a 0-100 risk score into standard threat levels."""
    if score >= 75:
        return "CRITICAL"
    elif score >= 55:
        return "HIGH"
    elif score >= 35:
        return "MODERATE"
    else:
        return "LOW"

def predict_multi_horizon_risk(df_risk):
    """
    Calculates +1h, +3h, and +6h flood risk projections.
    Formula considers current score, rainfall rate, and terrain elevation slope.
    """
    records = []
    for _, row in df_risk.iterrows():
        current_score = float(row.get('risk_score', 50))
        rain_mm = float(row.get('weather_rain_mm', 15.0))
        elevation_m = float(row.get('elevation_m', 850.0))
        
        # Terrain elevation accumulation factor (lower ground accumulates water faster)
        elev_factor = max(0.6, (1000.0 - elevation_m) / 180.0)
        rain_rate = max(0.5, rain_mm / 10.0)
        
        # Incremental risk deltas across horizons
        delta_1h = round(rain_rate * elev_factor * 2.5, 1)
        delta_3h = round(rain_rate * elev_factor * 6.5, 1)
        delta_6h = round(rain_rate * elev_factor * 12.0, 1)
        
        score_1h = min(100.0, current_score + delta_1h)
        score_3h = min(100.0, current_score + delta_3h)
        score_6h = min(100.0, current_score + delta_6h)
        
        records.append({
            'zone_id': row.get('zone_id'),
            'zone_name': row.get('zone_name'),
            'current_score': round(current_score, 1),
            'current_cat': get_risk_category(current_score),
            'score_1h': round(score_1h, 1),
            'cat_1h': get_risk_category(score_1h),
            'score_3h': round(score_3h, 1),
            'cat_3h': get_risk_category(score_3h),
            'score_6h': round(score_6h, 1),
            'cat_6h': get_risk_category(score_6h),
            'elevation_m': elevation_m,
            'rain_mm': rain_mm
        })
        
    return pd.DataFrame(records)

def create_forecast_trajectory_chart(df_forecast):
    """Generates a Plotly multi-horizon comparison bar chart for all localities."""
    chart_rows = []
    for _, r in df_forecast.iterrows():
        chart_rows.append({'Locality': r['zone_name'], 'Horizon': 'Current', 'Risk Score': r['current_score']})
        chart_rows.append({'Locality': r['zone_name'], 'Horizon': '+1 Hour', 'Risk Score': r['score_1h']})
        chart_rows.append({'Locality': r['zone_name'], 'Horizon': '+3 Hours', 'Risk Score': r['score_3h']})
        chart_rows.append({'Locality': r['zone_name'], 'Horizon': '+6 Hours', 'Risk Score': r['score_6h']})
        
    df_chart = pd.DataFrame(chart_rows)
    
    fig = px.bar(
        df_chart, 
        x='Locality', 
        y='Risk Score', 
        color='Horizon', 
        barmode='group',
        title='📈 Multi-Horizon Flood Escalation Forecast (+1h, +3h, +6h)',
        color_discrete_map={
            'Current': '#ffc107',
            '+1 Hour': '#fd7e14',
            '+3 Hours': '#e65100',
            '+6 Hours': '#dc3545'
        },
        text='Risk Score'
    )
    fig.update_layout(height=380, yaxis_range=[0, 105])
    return fig