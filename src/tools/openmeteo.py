from __future__ import annotations

import logging
from datetime import datetime, timedelta
import pandas as pd
import requests

log = logging.getLogger(__name__)

def get_weather_history(lat: float, lon: float, days: int = 7) -> pd.DataFrame:
    """
    Fetch historical weather data from Open-Meteo archive.
    """
    try:
        end_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        url = (
            "https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&"
            "daily=temperature_2m_mean,precipitation_sum,windspeed_10m_max&timezone=Asia/Kolkata"
        )
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        daily = data.get("daily", {})
        if not daily:
            return pd.DataFrame()
            
        df = pd.DataFrame({
            "date": daily.get("time", []),
            "temperature_mean": daily.get("temperature_2m_mean", []),
            "precipitation_sum": daily.get("precipitation_sum", []),
            "windspeed_max": daily.get("windspeed_10m_max", [])
        })
        return df
    except Exception as e:
        log.error(f"Error fetching weather data: {e}")
        return pd.DataFrame()
