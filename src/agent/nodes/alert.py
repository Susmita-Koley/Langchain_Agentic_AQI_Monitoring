from __future__ import annotations

import time
import logging
import json
from pathlib import Path

from src.agent.state import AgentState
from src.config import AQI_CRITICAL_THRESHOLD, AQI_WARNING_THRESHOLD, REPORTS_DIR

log = logging.getLogger(__name__)

def route_alert(state: AgentState) -> dict:
    """Determine overall alert level and save snapshot."""
    t0 = time.time()
    city_aqi = state.get("city_aqi", {})
    
    critical_cities = []
    warning_cities = []
    
    for city, aqi in city_aqi.items():
        if aqi is not None:
            if aqi >= AQI_CRITICAL_THRESHOLD:
                critical_cities.append(city)
            elif aqi >= AQI_WARNING_THRESHOLD:
                warning_cities.append(city)
                
    if critical_cities:
        alert_level = "CRITICAL"
    elif warning_cities:
        alert_level = "WARNING"
    else:
        alert_level = "SAFE"
        
    log.info(f"ALERT LEVEL: {alert_level} | Critical: {len(critical_cities)} | Warning: {len(warning_cities)}")
    
    # Save snapshot
    run_date = state.get("run_date")
    run_id = state.get("run_id")
    
    # Update timings for save
    timings = {**state.get("node_timings", {}), "route_alert": round(time.time() - t0, 2)}
    
    snapshot = dict(state)
    snapshot["alert_level"] = alert_level
    snapshot["critical_cities"] = critical_cities
    snapshot["warning_cities"] = warning_cities
    snapshot["node_timings"] = timings
    
    report_path = REPORTS_DIR / f"{run_date}_{run_id}.json"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)
        log.info(f"Saved run snapshot to {report_path}")
    except Exception as e:
        log.error(f"Failed to save report: {e}")
        
    return {
        "alert_level": alert_level,
        "critical_cities": critical_cities,
        "warning_cities": warning_cities,
        "node_timings": timings
    }
