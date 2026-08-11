#!/usr/bin/env python
from __future__ import annotations
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.basicConfig(level=logging.INFO, format='%(levelname)s | %(message)s')

from src.agent.graph import run_agent

if __name__ == '__main__':
    print('Starting AQ Monitoring Agent run...')
    result = run_agent()
    print(f'\n=== Run Complete ===')
    print(f'Alert Level : {result["alert_level"]}')
    print(f'Duration    : {result["run_duration_seconds"]}s')
    print(f'\nCity AQI:')
    for city, aqi in result['city_aqi'].items():
        print(f'  {city:12} AQI={aqi}')
    if result['anomaly_details']:
        print(f'\nAnomalies Detected:')
        for a in result['anomaly_details']:
            print(f'  {a}')
