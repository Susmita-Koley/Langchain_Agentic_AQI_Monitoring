from __future__ import annotations

import time
import logging
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.agent.state import AgentState
from src.tools.openaq import OpenAQClient
from src.config import OPENAQ_API_KEY, HISTORY_DAYS

log = logging.getLogger(__name__)

def detect_anomalies(state: AgentState) -> dict:
    """Detect anomalies using IsolationForest on historical data, and basic threshold checks."""
    t0 = time.time()
    client = OpenAQClient(api_key=OPENAQ_API_KEY)
    clean = state.get("clean_measurements", {})
    sensors = state.get("sensor_ids", {})
    
    anomaly_flags = {city: False for city in clean}
    anomaly_details = []
    
    for city, data in clean.items():
        pm25_val = data.get("pm25")
        if pm25_val is None:
            continue
            
        is_anomaly = False
        
        # 1. Simple Threshold
        if pm25_val > 150:
            is_anomaly = True
            anomaly_details.append({"city": city, "pollutant": "pm25", "value": pm25_val, "threshold": 150})
            
        # 2. IsolationForest
        city_sensors = sensors.get(city, {})
        pm25_sensor = city_sensors.get("pm25")
        
        if pm25_sensor:
            hist_data = client.get_historical_daily(pm25_sensor, days=HISTORY_DAYS)
            if len(hist_data) >= 3:
                df = pd.DataFrame(hist_data)
                df["value"] = pd.to_numeric(df["value"], errors="coerce")
                df = df.dropna()
                
                if len(df) >= 3:
                    # Train IsolationForest
                    X = df[["value"]].values
                    model = IsolationForest(contamination=0.15, random_state=42)
                    model.fit(X)
                    
                    # Predict on today's reading
                    pred = model.predict([[pm25_val]])
                    if pred[0] == -1:
                        is_anomaly = True
                        anomaly_details.append({
                            "city": city, 
                            "pollutant": "pm25", 
                            "value": pm25_val, 
                            "threshold": "ML Anomaly (IsolationForest)"
                        })
                        
        anomaly_flags[city] = is_anomaly
        
    summary_str = f"Detected {len(anomaly_details)} anomalies across {len([c for c, f in anomaly_flags.items() if f])} cities."
    log.info(summary_str)
    
    return {
        "anomaly_flags": anomaly_flags,
        "anomaly_details": anomaly_details,
        "anomaly_summary": summary_str,
        "node_timings": {**state.get("node_timings", {}), "detect_anomalies": round(time.time() - t0, 2)}
    }
