from __future__ import annotations

from typing import TypedDict, Optional, Any, List, Dict

class AgentState(TypedDict):
    run_id: str
    run_date: str  # ISO date YYYY-MM-DD
    
    # After fetch_data
    raw_measurements: dict  # city -> {pm25: float|None, pm10: float|None, no2: float|None, o3: float|None, location_name: str, location_id: int}
    fetch_errors: list  # cities that failed
    sensor_ids: dict  # city -> {pm25: sensor_id, ...}
    
    # After validate
    clean_measurements: dict  # city -> same structure, None for invalid
    validation_warnings: list  # warning strings
    city_aqi: dict  # city -> int (AQI score) or None
    
    # After detect_anomalies
    anomaly_flags: dict  # city -> bool
    anomaly_details: list  # list of {city, pollutant, value, threshold}
    anomaly_summary: str
    
    # After correlate_weather
    weather_data: dict  # city -> {temperature_mean, precipitation_sum, windspeed_max} for last 7 days
    pm25_correlation: dict  # {pearson_r: float, p_value: float, interpretation: str} or None
    
    # After route_alert
    alert_level: str  # 'SAFE' | 'WARNING' | 'CRITICAL'
    critical_cities: list
    warning_cities: list
    run_duration_seconds: float
    node_timings: dict  # node_name -> seconds
    langfuse_trace_url: str  # clickable URL to the trace in LangFuse dashboard
