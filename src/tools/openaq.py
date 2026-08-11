from __future__ import annotations

import time
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import requests

log = logging.getLogger(__name__)

class OpenAQClient:
    """Client for OpenAQ v3 API."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openaq.org/v3"
        self.headers = {"X-API-Key": self.api_key}

    def _request_with_retry(self, url: str) -> Optional[Dict[str, Any]]:
        """Make HTTP request with simple retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            time.sleep(0.3)  # Respect rate limits
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in [401, 404, 429]:
                    log.warning(f"OpenAQ API error {response.status_code} for {url}")
                    if response.status_code == 429 and attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return None
                response.raise_for_status()
            except Exception as e:
                log.error(f"Error fetching {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return None
        return None

    def find_nearest_location(self, lat: float, lon: float, radius_m: int = 25000) -> Optional[Dict[str, Any]]:
        """Find nearest active station with sensors."""
        url = f"{self.base_url}/locations?coordinates={lat},{lon}&radius={radius_m}&limit=5"
        data = self._request_with_retry(url)
        if data and data.get("results"):
            for loc in data["results"]:
                if loc.get("sensors"):
                    return loc
        return None

    def get_latest_measurements(self, location_id: int) -> list[dict]:
        """Get latest measurements for a location (may return null values for stale stations)."""
        url = f"{self.base_url}/locations/{location_id}/latest"
        data = self._request_with_retry(url)
        results = []
        if data and data.get("results"):
            for res in data["results"]:
                param = res.get("parameter", {}).get("name", "")
                val = res.get("value")
                unit = res.get("parameter", {}).get("units", "")
                dt_utc = res.get("datetime", {}).get("utc", "")
                sensor_id = res.get("sensors_id")
                if val is not None:
                    results.append({
                        "parameter": param,
                        "value": float(val),
                        "unit": unit,
                        "datetime_utc": dt_utc,
                        "sensor_id": sensor_id
                    })
        return results

    def get_recent_measurement(self, sensor_id: int, hours: int = 48) -> Optional[float]:
        """Get the most recent non-null measurement from hourly data over the last N hours.

        More reliable than /latest which only shows data updated within the last few minutes.
        The measurements endpoint has historical data even for stations with stale 'latest' values.
        """
        now = datetime.utcnow()
        date_from = (now - timedelta(hours=hours)).strftime('%Y-%m-%d')
        date_to = now.strftime('%Y-%m-%d')
        url = (
            f"{self.base_url}/sensors/{sensor_id}/measurements"
            f"?period_name=hour&date_from={date_from}&date_to={date_to}&limit={hours + 5}"
        )
        data = self._request_with_retry(url)
        if not (data and data.get("results")):
            return None

        # Find the most recent non-null value (results may be in any order)
        best_val: Optional[float] = None
        best_dt = ""
        for result in data["results"]:
            val = result.get("value")
            dt = result.get("period", {}).get("datetimeTo", {}).get("utc", "")
            if val is not None and dt > best_dt:
                best_val = float(val)
                best_dt = dt
        return best_val

    def get_historical_daily(self, sensor_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily aggregated measurements for a sensor."""
        today = datetime.utcnow().strftime('%Y-%m-%d')
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')
        url = f"{self.base_url}/sensors/{sensor_id}/measurements?period_name=day&date_from={start_date}&date_to={today}&limit={days * 2}"
        data = self._request_with_retry(url)
        results = []
        if data and data.get("results"):
            for res in data["results"]:
                val = res.get("value")
                dt = res.get("period", {}).get("datetimeTo", {}).get("utc", "")
                if val is not None and dt:
                    results.append({
                        "date": dt[:10],
                        "value": float(val)
                    })
        return results
