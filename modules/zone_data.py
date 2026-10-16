"""
modules/zone_data.py
Builds the zone table the dashboard uses.

Curated path (default): data/zones.csv + weather pipeline + modules.risk_engine
    -> deterministic and explainable; the Risk Weight Tuner is actually applied.
Simulated path: zones generated around a GPS point (random values); operator
    overrides are re-applied on every run.
"""
import pandas as pd

from modules.gis import load_zone_data
from modules.risk_engine import calculate_zone_risk
from modules.weather import get_zone_weather

WEIGHT_KEYS = ("flood", "population", "weather", "accessibility", "infrastructure")


def normalize_weights(weights):
    """Scale slider weights so they sum to 1.0 (all zero -> defaults)."""
    total = sum(max(0.0, float(weights.get(k, 0.0))) for k in WEIGHT_KEYS)
    if total <= 0:
        return {"flood": 0.35, "population": 0.25, "weather": 0.15, "accessibility": 0.15, "infrastructure": 0.10}
    return {k: max(0.0, float(weights.get(k, 0.0))) / total for k in WEIGHT_KEYS}


def build_curated_zones(weights, overrides=None, allow_live=False):
    """Return (df_risk, weather_sources) from data/zones.csv."""
    overrides = overrides or {}
    w = normalize_weights(weights)
    rows, sources = [], set()
    for _, r in load_zone_data().iterrows():
        zid = r["zone_id"]
        flood = float(overrides.get(zid, r["flood_severity"]))
        wx = get_zone_weather(r["latitude"], r["longitude"], zone_id=zid, allow_live=allow_live)
        sources.add(wx["source"])
        risk = calculate_zone_risk(flood, r["population_exposure"], wx["weather_risk"],
                                   r["road_accessibility"], r["infrastructure_exposure"], weights=w)
        rows.append({
            **r.to_dict(),
            "flood_severity": flood,
            "flood_overridden": zid in overrides,
            "weather_temp": wx["temperature"],
            "weather_rain_mm": wx["rainfall_mm"],
            "weather_risk": wx["weather_risk"],
            "weather_desc": wx["description"],
            "weather_source": wx["source"],
            "risk_score": risk["total_score"],
            "risk_category": risk["category"],
            "breakdown": risk["breakdown"],
        })
    return pd.DataFrame(rows), sources


def apply_overrides_simulated(df_risk, overrides):
    """Re-apply drone-derived flood severity to the simulated zone table (on a copy)."""
    df = df_risk.copy()
    for zid, sev in (overrides or {}).items():
        hit = df.index[df["zone_id"] == zid]
        if len(hit) == 0:
            continue
        i = hit[0]
        pop, rain = df.at[i, "population_density"], df.at[i, "weather_rain_mm"]
        score = int(min(99, max(15, sev * 0.45 + (pop / 250) * 0.35 + (rain / 1.5) * 0.2)))
        df.at[i, "flood_severity"] = sev
        df.at[i, "risk_score"] = score
        df.at[i, "risk_category"] = "CRITICAL" if score >= 75 else "HIGH" if score >= 55 else "MODERATE"
    return df


def explain_zone(row, sos_requests=None, detections=None):
    """
    Plain-language reasons for a zone's risk level, built ONLY from values in the system.
    Returns a list of strings.
    """
    name = row["zone_name"]
    lines = [f"Flood severity {row['flood_severity']:.0f}%"
             + (" (updated from drone analysis)" if row.get("flood_overridden") else "")]
    if "population_exposure" in row.index:
        lines.append(f"Population exposure {row['population_exposure']:.0f}/100")
    if "road_accessibility" in row.index:
        acc = float(row["road_accessibility"])
        lines.append(f"Road accessibility {acc:.0f}/100" + (" — main access impaired" if acc < 40 else ""))
    if "weather_rain_mm" in row.index:
        src = row.get("weather_source", "weather data")
        lines.append(f"Rainfall {row['weather_rain_mm']} mm/h ({src})")
    sos_n = len([s for s in (sos_requests or []) if s.get("locality") == name and s.get("status") == "ACTIVE"])
    if sos_n:
        lines.append(f"{sos_n} active SOS request(s) in this sector")
    det = [d for d in (detections or []) if d.get("sector") == name]
    if det:
        persons = len([d for d in det if d.get("group") == "person"])
        ver = len([d for d in det if d.get("status") == "VERIFIED"])
        lines.append(f"{persons} person detection(s) logged, {ver} verified by a human (AI output, unverified unless confirmed)")
    return lines
