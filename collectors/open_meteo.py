from __future__ import annotations

import json
import pathlib
from datetime import date, timedelta
from typing import Any

import requests

from config import (
    MUMBAI_STATIONS,
    OPEN_METEO_ARCHIVE_URL,
    OPEN_METEO_FORECAST_URL,
    RAW_DIR,
    parse_monsoon_start,
)

TIMEOUT_SECONDS = 30


def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def _write_json(path: str, payload: Any) -> None:
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)


def collect_archive(today: date | None = None) -> list[dict[str, Any]]:
    """Collect chronological daily rainfall from monsoon start to yesterday.

    Open-Meteo's archive endpoint is no-key and supports daily precipitation.
    If the archive API has not yet materialised very recent days, the caller can
    still use collect_forecast() for today and coming days.
    """
    today = today or date.today()
    start = parse_monsoon_start()
    end = max(start, today - timedelta(days=1))
    results: list[dict[str, Any]] = []

    for station in MUMBAI_STATIONS:
        params = {
            "latitude": station.latitude,
            "longitude": station.longitude,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": "precipitation_sum,precipitation_hours,temperature_2m_max,temperature_2m_min,wind_speed_10m_max",
            "timezone": "Asia/Kolkata",
        }
        try:
            data = _get_json(OPEN_METEO_ARCHIVE_URL, params)
            data["station"] = station.__dict__
            data["collector_status"] = "ok"
        except Exception as exc:  # fail-safe for static dashboard generation
            data = {
                "station": station.__dict__,
                "collector_status": "error",
                "error": str(exc),
                "daily": {"time": []},
            }
        results.append(data)

    _write_json(f"{RAW_DIR}/open_meteo_archive.json", results)
    return results


def collect_forecast() -> list[dict[str, Any]]:
    """Collect current and forward-looking precipitation signals."""
    results: list[dict[str, Any]] = []
    for station in MUMBAI_STATIONS:
        params = {
            "latitude": station.latitude,
            "longitude": station.longitude,
            "hourly": "precipitation,rain,weather_code,wind_speed_10m",
            "daily": "precipitation_sum,precipitation_probability_max,weather_code,wind_speed_10m_max",
            "current": "precipitation,rain,weather_code,wind_speed_10m",
            "timezone": "Asia/Kolkata",
            "forecast_days": 7,
            "past_days": 2,
        }
        try:
            data = _get_json(OPEN_METEO_FORECAST_URL, params)
            data["station"] = station.__dict__
            data["collector_status"] = "ok"
        except Exception as exc:
            data = {
                "station": station.__dict__,
                "collector_status": "error",
                "error": str(exc),
                "daily": {"time": []},
                "hourly": {"time": []},
            }
        results.append(data)

    _write_json(f"{RAW_DIR}/open_meteo_forecast.json", results)
    return results


def main() -> None:
    collect_archive()
    collect_forecast()


if __name__ == "__main__":
    main()
