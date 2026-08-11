from __future__ import annotations

import math

from src.config import PM25_BREAKPOINTS

def compute_aqi(pm25: float) -> tuple[int, str, str]:
    """
    Compute US EPA AQI for PM2.5.
    Returns (aqi_score, category, color_hex).
    """
    if pm25 < 0:
        return 0, "Good", "#00E400"
    
    # PM2.5 values are truncated to 1 decimal place
    pm25_trunc = math.floor(pm25 * 10) / 10.0
    
    for c_low, c_high, i_low, i_high, category, color in PM25_BREAKPOINTS:
        if c_low <= pm25_trunc <= c_high:
            # Formula: (I_high - I_low) / (C_high - C_low) * (C - C_low) + I_low
            aqi = ((i_high - i_low) / (c_high - c_low)) * (pm25_trunc - c_low) + i_low
            return round(aqi), category, color
            
    # If above max (500.4)
    c_low, c_high, i_low, i_high, category, color = PM25_BREAKPOINTS[-1]
    aqi = ((i_high - i_low) / (c_high - c_low)) * (pm25_trunc - c_low) + i_low
    return round(aqi), category, color

def aqi_category(aqi: int) -> str:
    """Return AQI category for a given score."""
    for c_low, c_high, i_low, i_high, category, color in PM25_BREAKPOINTS:
        if i_low <= aqi <= i_high:
            return category
    return "Hazardous"

def aqi_color(aqi: int) -> str:
    """Return AQI color hex for a given score."""
    for c_low, c_high, i_low, i_high, category, color in PM25_BREAKPOINTS:
        if i_low <= aqi <= i_high:
            return color
    return "#7E0023"
