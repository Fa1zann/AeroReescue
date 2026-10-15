"""
modules/search_priority.py
Calculates combined Search & Rescue dispatch priorities fusing current risk,
future projected risk, population exposure, and active SOS requests.
"""

import pandas as pd

def calculate_search_priorities(df_risk, df_forecast, sos_requests):
    """
    Fuses current risk, predicted risk escalation (+3h), population exposure,
    and active SOS emergency alerts into a single Search Priority Score (0-100).
    """
    priority_list = []
    
    # Extract localities with active SOS requests
    sos_localities = set()
    if sos_requests:
        for sos in sos_requests:
            if sos.get("status") == "ACTIVE":
                sos_localities.add(sos.get("locality"))

    for _, row in df_risk.iterrows():
        zone_id = row['zone_id']
        name = row['zone_name']
        current_score = float(row.get('risk_score', 50))
        pop_exp = float(row.get('population_exposure', 50))
        
        # Match forecast data if available
        score_3h = current_score
        if not df_forecast.empty and 'zone_id' in df_forecast.columns:
            f_match = df_forecast[df_forecast['zone_id'] == zone_id]
            if not f_match.empty:
                score_3h = float(f_match.iloc[0]['score_3h'])
        
        # Composite Base Priority = 40% Current Risk + 30% Projected 3h Risk + 30% Population Exposure
        priority_score = (current_score * 0.4) + (score_3h * 0.3) + (pop_exp * 0.3)
        
        reasons = []
        has_sos = name in sos_localities
        
        # Active SOS Signal Bonus (+15 points)
        if has_sos:
            priority_score += 15.0
            reasons.append("🚨 ACTIVE SOS Emergency Signal")
            
        if score_3h >= 75:
            reasons.append("🔮 Predicted Critical Surge (+3h)")
        elif score_3h > current_score + 5:
            reasons.append("📈 Rapid Flood Escalation Trend")
            
        if pop_exp >= 70:
            reasons.append("👥 High Population Density")
            
        if not reasons:
            reasons.append("Standard Sector Monitoring")

        final_priority = min(100.0, round(priority_score, 1))
        
        priority_list.append({
            'zone_id': zone_id,
            'zone_name': name,
            'search_priority': final_priority,
            'current_score': current_score,
            'predicted_3h': score_3h,
            'has_active_sos': has_sos,
            'reasons': " | ".join(reasons)
        })

    df_prio = pd.DataFrame(priority_list)
    return df_prio.sort_values(by='search_priority', ascending=False)