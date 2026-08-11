from __future__ import annotations

import time
import logging
import numpy as np

from src.agent.state import AgentState
from src.tools.aqi import compute_aqi
from src.config import POLLUTANTS

log = logging.getLogger(__name__)

# Valid ranges
LIMITS = {
    "pm25": (0, 500),
    "pm10": (0, 600),
    "no2": (0, 2000),
    "o3": (0, 500)
}

def validate(state: AgentState) -> dict:
    """Validate data limits and compute basic AQI."""
    t0 = time.time()
    raw = state.get("raw_measurements", {})
    
    clean_measurements = {}
    validation_warnings = []
    city_aqi = {}
    
    # Structure for Z-score checks
    pollutant_arrays = {p: [] for p in POLLUTANTS}
    pollutant_map = {p: [] for p in POLLUTANTS}  # (city, value)
    
    for city, data in raw.items():
        clean_data = {"location_name": data.get("location_name"), "location_id": data.get("location_id")}
        is_valid_city = True
        
        for p in POLLUTANTS:
            val = data.get(p)
            if val is not None:
                min_v, max_v = LIMITS.get(p, (0, float('inf')))
                if not (min_v <= val <= max_v):
                    validation_warnings.append(f"{city} {p} out of bounds: {val}")
                    clean_data[p] = None
                else:
                    clean_data[p] = val
                    pollutant_arrays[p].append(val)
                    pollutant_map[p].append((city, val))
            else:
                clean_data[p] = None
                
        clean_measurements[city] = clean_data
        
        pm25 = clean_data.get("pm25")
        if pm25 is not None:
            aqi, cat, color = compute_aqi(pm25)
            city_aqi[city] = aqi
        else:
            city_aqi[city] = None
            
    # Z-score check
    for p in POLLUTANTS:
        arr = pollutant_arrays[p]
        if len(arr) > 2:
            mean = np.mean(arr)
            std = np.std(arr)
            if std > 0:
                for city, val in pollutant_map[p]:
                    z = abs((val - mean) / std)
                    if z > 3:
                        validation_warnings.append(f"Z-Score Warning: {city} {p}={val} (Z={z:.2f})")
                        
    return {
        "clean_measurements": clean_measurements,
        "validation_warnings": validation_warnings,
        "city_aqi": city_aqi,
        "node_timings": {**state.get("node_timings", {}), "validate": round(time.time() - t0, 2)}
    }
