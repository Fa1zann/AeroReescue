"""
modules/risk_engine.py
Calculates explainable risk scores, threat levels, and factor breakdowns.
"""

def calculate_zone_risk(flood_sev, pop_exp, weather_risk, road_access, infra_exp, weights=None):
    """
    Calculates a 0-100 explainable risk score and categorization.
    
    Parameters:
        flood_sev (float): Flood extent severity (0-100)
        pop_exp (float): Population density exposure (0-100)
        weather_risk (float): Weather forecast risk score (0-100)
        road_access (float): Road accessibility index (0-100, where 100 is fully open)
        infra_exp (float): Infrastructure impact score (0-100)
        weights (dict, optional): Custom factor weights summing to 1.0
        
    Returns:
        dict: Contains total_score, category, color, and factor breakdown
    """
    # Set default heuristic weights if none provided
    if weights is None:
        weights = {
            'flood': 0.35,
            'population': 0.25,
            'weather': 0.15,
            'accessibility': 0.15,
            'infrastructure': 0.10
        }

    # Invert road accessibility: lower accessibility = higher risk hazard
    inaccessibility_hazard = max(0.0, min(100.0, 100.0 - float(road_access)))

    # Compute individual factor contributions
    c_flood = float(flood_sev) * weights['flood']
    c_pop = float(pop_exp) * weights['population']
    c_weather = float(weather_risk) * weights['weather']
    c_access = inaccessibility_hazard * weights['accessibility']
    c_infra = float(infra_exp) * weights['infrastructure']

    # Total score calculation (bounded 0 to 100)
    raw_score = c_flood + c_pop + c_weather + c_access + c_infra
    total_score = round(max(0.0, min(100.0, raw_score)), 1)

    # Determine risk category and color badge
    if total_score <= 30.0:
        category = "LOW"
        color = "#28a745" # Green
    elif total_score <= 55.0:
        category = "MODERATE"
        color = "#ffc107" # Yellow
    elif total_score <= 75.0:
        category = "HIGH"
        color = "#fd7e14" # Orange
    else:
        category = "CRITICAL"
        color = "#dc3545" # Red

    # Detailed point breakdown for explainability
    breakdown = {
        "Flood Extent (+35%)": round(c_flood, 1),
        "Population Density (+25%)": round(c_pop, 1),
        "Weather Forecast (+15%)": round(c_weather, 1),
        "Road Inaccessibility (+15%)": round(c_access, 1),
        "Critical Infrastructure (+10%)": round(c_infra, 1)
    }

    return {
        "total_score": total_score,
        "category": category,
        "color": color,
        "breakdown": breakdown
    }