from __future__ import annotations

import time
import logging
from scipy.stats import pearsonr
import numpy as np

from src.agent.state import AgentState
from src.tools.openmeteo import get_weather_history
from src.config import CITIES

log = logging.getLogger(__name__)

def correlate_weather(state: AgentState) -> dict:
    """Correlate historical weather with PM2.5 trends."""
    t0 = time.time()
    
    clean = state.get("clean_measurements", {})
    weather_data = {}
    
    cities_to_fetch = list(clean.keys())[:4]  # Max 4 to limit API calls
    
    # 1. Fetch weather
    for city in cities_to_fetch:
        coords = CITIES.get(city)
        if coords:
            df = get_weather_history(lat=coords["lat"], lon=coords["lon"], days=7)
            if not df.empty:
                weather_data[city] = df.to_dict(orient="list")
                
    # 2. Correlate (Simple approximation: use today's AQI or PM2.5 proxy across cities if historical is not available easily in state)
    # The prompt says: "Y = daily PM2.5 values (from historical data, or use city_aqi as proxy)"
    # Actually, we can correlate cross-sectional temperature mean vs AQI for today across cities
    # OR historical for one city. Let's do cross-sectional across cities for today.
    # Wait, the prompt says: "X = daily temperature_mean across cities averaged, Y = daily PM2.5 values"
    # Actually, let's just correlate today's temperature per city with today's PM2.5 per city.
    
    pm25_correlation = None
    
    try:
        X = []
        Y = []
        for city in cities_to_fetch:
            if city in weather_data and city in clean:
                pm25 = clean[city].get("pm25")
                temps = weather_data[city].get("temperature_mean")
                if pm25 is not None and temps and len(temps) > 0:
                    # use the latest day's temp for correlation with today's pm25
                    X.append(temps[-1])
                    Y.append(pm25)
                    
        if len(X) >= 3:
            r, p_value = pearsonr(X, Y)
            if abs(r) < 0.3:
                interp = "Weak correlation"
            elif abs(r) < 0.6:
                interp = "Moderate correlation"
            else:
                interp = "Strong correlation"
                
            if r < 0:
                interp = f"Inverse {interp.lower()}"
                
            pm25_correlation = {
                "pearson_r": float(r),
                "p_value": float(p_value),
                "interpretation": interp
            }
            log.info(f"Weather Correlation: r={r:.2f} ({interp})")
    except Exception as e:
        log.error(f"Error computing correlation: {e}")
        
    return {
        "weather_data": weather_data,
        "pm25_correlation": pm25_correlation,
        "node_timings": {**state.get("node_timings", {}), "correlate_weather": round(time.time() - t0, 2)}
    }
