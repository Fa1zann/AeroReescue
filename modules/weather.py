"""
modules/weather.py
Fetches weather forecasts with live API integration and local offline fallbacks.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(BASE_DIR, "data", "weather_cache.json")

# Tier 3: Default Demo Scenario Data
DEFAULT_DEMO_WEATHER = {
    "temperature": 27.0,
    "humidity": 85,
    "rainfall_mm": 25.0,
    "weather_risk": 60,
    "description": "Monsoon Downpour (Demo)",
    "source": "Demo Scenario Data"
}

def get_zone_weather(lat, lon, zone_id="Z1"):
    """
    3-Tier Weather Pipeline:
    1. Live OpenWeatherMap API call
    2. Local JSON file cache
    3. Default Demo Scenario
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")

    # -------------------------------------------------------------------------
    # TIER 1: LIVE OPENWEATHERMAP API
    # -------------------------------------------------------------------------
    if api_key and api_key != "YOUR_API_KEY_HERE" and api_key != "your_actual_api_key_here":
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        try:
            response = requests.get(url, timeout=3.5)
            if response.status_code == 200:
                data = response.json()
                
                # Extract hourly rain volume if present
                rain_1h = data.get("rain", {}).get("1h", 0.0)
                humidity = data.get("main", {}).get("humidity", 50)
                temp = data.get("main", {}).get("temp", 25.0)
                desc = data.get("weather", [{}])[0].get("description", "clear")

                # Compute 0-100 weather risk score based on rainfall rate & humidity
                calc_risk = min(100, int((rain_1h * 12.0) + (humidity * 0.4)))

                return {
                    "temperature": round(temp, 1),
                    "humidity": humidity,
                    "rainfall_mm": round(rain_1h, 1),
                    "weather_risk": calc_risk,
                    "description": desc.title(),
                    "source": "Live OpenWeather API"
                }
        except Exception:
            pass  # Fall through smoothly to Tier 2 on internet failure or timeout

    # -------------------------------------------------------------------------
    # TIER 2: LOCAL JSON CACHE
    # -------------------------------------------------------------------------
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r") as f:
                cache_data = json.load(f)
                if zone_id in cache_data:
                    z_weather = cache_data[zone_id]
                    return {
                        "temperature": z_weather.get("temperature", 26.0),
                        "humidity": z_weather.get("humidity", 80),
                        "rainfall_mm": z_weather.get("rainfall_mm", 20.0),
                        "weather_risk": z_weather.get("weather_risk", 50),
                        "description": z_weather.get("description", "Cached Storm").title(),
                        "source": "Cached Weather Data"
                    }
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # TIER 3: DEMO SCENARIO FALLBACK
    # -------------------------------------------------------------------------
    return DEFAULT_DEMO_WEATHER.copy()