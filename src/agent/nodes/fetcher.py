from __future__ import annotations

import time
import logging

from src.agent.state import AgentState
from src.config import CITIES, POLLUTANTS, STATION_SEARCH_RADIUS, OPENAQ_API_KEY
from src.tools.openaq import OpenAQClient

log = logging.getLogger(__name__)


def fetch_data(state: AgentState) -> dict:
    """Fetch recent OpenAQ measurements for all configured cities.

    Strategy:
    1. Find nearest station for each city (by lat/lon + radius).
    2. Extract sensor IDs directly from the location object (no extra API call).
    3. For each pollutant sensor, fetch the most recent hourly value from the
       last 48 hours — this is far more reliable than the /latest endpoint,
       which only returns data if the station updated within the last few minutes.
    """
    t0 = time.time()
    client = OpenAQClient(api_key=OPENAQ_API_KEY)

    raw_measurements: dict = {}
    fetch_errors: list = []
    sensor_ids: dict = {}

    for city, coords in CITIES.items():
        try:
            lat, lon = coords["lat"], coords["lon"]

            # ── Step 1: find nearest station ──────────────────────────────
            station = client.find_nearest_location(lat, lon, radius_m=STATION_SEARCH_RADIUS)
            if not station:
                log.warning(f"No station found for {city}")
                fetch_errors.append(city)
                continue

            loc_id   = station["id"]
            loc_name = station.get("name", "Unknown Station")

            # ── Step 2: extract sensor IDs from location object ───────────
            # The location response already contains sensor info — no extra call needed.
            city_sensors: dict = {}
            for sensor in station.get("sensors", []):
                param_name = sensor.get("parameter", {}).get("name", "").lower()
                if param_name in POLLUTANTS:
                    city_sensors[param_name] = sensor["id"]

            if not city_sensors:
                log.warning(f"No pollutant sensors found at {loc_name} for {city}")
                fetch_errors.append(city)
                continue

            # ── Step 3: fetch most recent hourly value per pollutant ──────
            city_data: dict = {p: None for p in POLLUTANTS}
            city_data["location_name"] = loc_name
            city_data["location_id"]   = loc_id

            for param, sensor_id in city_sensors.items():
                val = client.get_recent_measurement(sensor_id, hours=48)
                city_data[param] = val

            raw_measurements[city] = city_data
            sensor_ids[city]       = city_sensors

            log.info(
                f"[ {city} ] {loc_name} | "
                f"PM2.5: {city_data.get('pm25')} µg/m³ | "
                f"PM10: {city_data.get('pm10')} µg/m³"
            )

        except Exception as e:
            log.error(f"Error fetching data for {city}: {e}")
            fetch_errors.append(city)

    return {
        "raw_measurements": raw_measurements,
        "fetch_errors":      fetch_errors,
        "sensor_ids":        sensor_ids,
        "node_timings":      {**state.get("node_timings", {}), "fetch_data": round(time.time() - t0, 2)},
    }
