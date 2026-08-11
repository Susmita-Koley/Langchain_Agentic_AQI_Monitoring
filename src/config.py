"""
config.py — Project 2: Autonomous Air Quality Monitoring Agent

Central configuration: cities, AQI thresholds, API credentials, paths.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ── Project root & .env ───────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# ── API Keys ──────────────────────────────────────────────────────────────────
OPENAQ_API_KEY      = os.getenv("OPENAQ_API_KEY", "")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST       = os.getenv("LANGFUSE_HOST", "https://eu.cloud.langfuse.com")

# ── Cities monitored ──────────────────────────────────────────────────────────
# Major Indian cities with consistent OpenAQ monitoring station coverage.
CITIES: dict[str, dict] = {
    "Delhi":     {"lat": 28.6139, "lon": 77.2090},
    "Mumbai":    {"lat": 19.0760, "lon": 72.8777},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946},
    "Chennai":   {"lat": 13.0827, "lon": 80.2707},
    "Kolkata":   {"lat": 22.5726, "lon": 88.3639},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "Pune":      {"lat": 18.5204, "lon": 73.8567},
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714},
}

# ── US EPA AQI breakpoints (PM2.5 µg/m³, 24-hour avg) ────────────────────────
# Source: https://www.epa.gov/sites/default/files/2016-04/documents/2012_aqi_factsheet.pdf
PM25_BREAKPOINTS = [
    # (C_low, C_high, I_low, I_high, category, color)
    (0.0,    12.0,   0,   50,  "Good",                       "#00E400"),
    (12.1,   35.4,  51,  100,  "Moderate",                   "#FFFF00"),
    (35.5,   55.4, 101,  150,  "Unhealthy for Sensitive",    "#FF7E00"),
    (55.5,  150.4, 151,  200,  "Unhealthy",                  "#FF0000"),
    (150.5, 250.4, 201,  300,  "Very Unhealthy",             "#8F3F97"),
    (250.5, 500.4, 301,  500,  "Hazardous",                  "#7E0023"),
]

# ── Alert thresholds ──────────────────────────────────────────────────────────
AQI_WARNING_THRESHOLD  = 100   # Any city AQI >= this → WARNING
AQI_CRITICAL_THRESHOLD = 200   # Any city AQI >= this → CRITICAL

# ── OpenAQ parameters of interest ─────────────────────────────────────────────
# These are parameter names as returned by the OpenAQ v3 API.
POLLUTANTS = ["pm25", "pm10", "no2", "o3"]

# Radius (metres) to search for monitoring stations around each city centre
STATION_SEARCH_RADIUS = 25_000   # 25 km

# Days of history to fetch for IsolationForest training
HISTORY_DAYS = 7

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR    = ROOT / "data"
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
