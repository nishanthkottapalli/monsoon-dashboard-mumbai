from __future__ import annotations

import json
import pathlib
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from config import NORMALIZED_DIR, RAW_DIR, parse_monsoon_start


def _read_json(path: str, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def _write_json(path: str, payload: Any) -> None:
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)


def rainfall_severity(mm: float) -> str:
    if mm >= 150:
        return "severe"
    if mm >= 100:
        return "high"
    if mm >= 60:
        return "moderate"
    if mm >= 20:
        return "watch"
    return "normal"


def normalize_archive() -> list[dict[str, Any]]:
    raw = _read_json(f"{RAW_DIR}/open_meteo_archive.json", [])
    observations: list[dict[str, Any]] = []

    for station_payload in raw:
        station = station_payload.get("station", {})
        daily = station_payload.get("daily", {}) or {}
        times = daily.get("time", []) or []
        for idx, day in enumerate(times):
            precip = float((daily.get("precipitation_sum") or [0])[idx] or 0)
            obs = {
                "id": f"daily-{station.get('name','station').lower()}-{day}",
                "type": "daily_rainfall",
                "source": "open_meteo_archive",
                "observed_date": day,
                "location": station,
                "value": {
                    "precipitation_sum_mm": precip,
                    "precipitation_hours": (daily.get("precipitation_hours") or [None])[idx],
                    "temperature_2m_max_c": (daily.get("temperature_2m_max") or [None])[idx],
                    "temperature_2m_min_c": (daily.get("temperature_2m_min") or [None])[idx],
                    "wind_speed_10m_max_kmh": (daily.get("wind_speed_10m_max") or [None])[idx],
                },
                "severity": rainfall_severity(precip),
                "confidence": "medium" if station_payload.get("collector_status") == "ok" else "low",
            }
            observations.append(obs)

    observations.sort(key=lambda x: (x["observed_date"], x["location"].get("name", "")))
    _write_json(f"{NORMALIZED_DIR}/weather_observations.json", observations)
    return observations


def normalize_forecast() -> dict[str, Any]:
    raw = _read_json(f"{RAW_DIR}/open_meteo_forecast.json", [])
    forecasts = []
    current = []
    for station_payload in raw:
        station = station_payload.get("station", {})
        daily = station_payload.get("daily", {}) or {}
        for idx, day in enumerate(daily.get("time", []) or []):
            precip = float((daily.get("precipitation_sum") or [0])[idx] or 0)
            forecasts.append({
                "type": "daily_forecast",
                "source": "open_meteo_forecast",
                "forecast_date": day,
                "location": station,
                "value": {
                    "precipitation_sum_mm": precip,
                    "precipitation_probability_max_pct": (daily.get("precipitation_probability_max") or [None])[idx],
                    "weather_code": (daily.get("weather_code") or [None])[idx],
                    "wind_speed_10m_max_kmh": (daily.get("wind_speed_10m_max") or [None])[idx],
                },
                "severity": rainfall_severity(precip),
                "confidence": "medium" if station_payload.get("collector_status") == "ok" else "low",
            })
        cur = station_payload.get("current") or {}
        if cur:
            rain = float(cur.get("rain") or cur.get("precipitation") or 0)
            current.append({
                "type": "current_weather",
                "source": "open_meteo_forecast",
                "observed_at": cur.get("time"),
                "location": station,
                "value": {
                    "rain_mm": rain,
                    "precipitation_mm": cur.get("precipitation"),
                    "weather_code": cur.get("weather_code"),
                    "wind_speed_10m_kmh": cur.get("wind_speed_10m"),
                },
                "severity": rainfall_severity(rain * 24),
                "confidence": "medium" if station_payload.get("collector_status") == "ok" else "low",
            })
    forecasts.sort(key=lambda x: (x["forecast_date"], x["location"].get("name", "")))
    payload = {"current": current, "daily": forecasts}
    _write_json(f"{NORMALIZED_DIR}/weather_forecast.json", payload)
    return payload


def build_chronological_daily_series(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for obs in observations:
        grouped[obs["observed_date"]].append(obs)

    start = parse_monsoon_start()
    end = date.today()
    ordered = []
    day = start
    while day <= end:
        key = day.isoformat()
        rows = grouped.get(key, [])
        values = [r["value"]["precipitation_sum_mm"] for r in rows]
        max_mm = max(values) if values else 0.0
        avg_mm = round(sum(values) / len(values), 2) if values else 0.0
        ordered.append({
            "date": key,
            "rainfall_mm_max": round(max_mm, 2),
            "rainfall_mm_avg": avg_mm,
            "severity": rainfall_severity(max_mm),
            "stations": rows,
        })
        day = day.fromordinal(day.toordinal() + 1)
    return ordered


def main() -> None:
    observations = normalize_archive()
    normalize_forecast()
    daily = build_chronological_daily_series(observations)
    _write_json(f"{NORMALIZED_DIR}/daily_weather_series.json", daily)


if __name__ == "__main__":
    main()
