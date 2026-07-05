from __future__ import annotations

import json
import pathlib
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from config import IST, NORMALIZED_DIR, RAW_DIR, parse_monsoon_start, today_ist


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


def _safe_list(values: Any) -> list[Any]:
    return values if isinstance(values, list) else []


def _value_at(values: Any, idx: int, default: Any = None) -> Any:
    seq = _safe_list(values)
    if idx >= len(seq):
        return default
    return seq[idx]


def _parse_open_meteo_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Open-Meteo returns local times without an offset when timezone is set.
        return datetime.fromisoformat(value).replace(tzinfo=IST)
    except ValueError:
        return None


def _rain_value_mm(hourly: dict[str, Any], idx: int) -> float:
    # Prefer total precipitation; fall back to rain when precipitation is absent.
    precipitation = _value_at(hourly.get("precipitation"), idx, None)
    rain = _value_at(hourly.get("rain"), idx, None)
    showers = _value_at(hourly.get("showers"), idx, None)
    value = precipitation if precipitation is not None else rain if rain is not None else showers
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def normalize_archive() -> list[dict[str, Any]]:
    raw = _read_json(f"{RAW_DIR}/open_meteo_archive.json", [])
    observations: list[dict[str, Any]] = []

    for station_payload in raw:
        station = station_payload.get("station", {})
        daily = station_payload.get("daily", {}) or {}
        times = daily.get("time", []) or []
        for idx, day in enumerate(times):
            precip = float(_value_at(daily.get("precipitation_sum"), idx, 0) or 0)
            obs = {
                "id": f"daily-{station.get('name','station').lower()}-{day}",
                "type": "daily_rainfall",
                "source": "open_meteo_archive",
                "observed_date": day,
                "location": station,
                "value": {
                    "precipitation_sum_mm": precip,
                    "precipitation_hours": _value_at(daily.get("precipitation_hours"), idx),
                    "temperature_2m_max_c": _value_at(daily.get("temperature_2m_max"), idx),
                    "temperature_2m_min_c": _value_at(daily.get("temperature_2m_min"), idx),
                    "wind_speed_10m_max_kmh": _value_at(daily.get("wind_speed_10m_max"), idx),
                },
                "severity": rainfall_severity(precip),
                "confidence": "medium" if station_payload.get("collector_status") == "ok" else "low",
            }
            observations.append(obs)

    observations.sort(key=lambda x: (x["observed_date"], x["location"].get("name", "")))
    _write_json(f"{NORMALIZED_DIR}/weather_observations.json", observations)
    return observations


def _build_station_nowcast(station: dict[str, Any], hourly: dict[str, Any], current: dict[str, Any], status: str) -> dict[str, Any]:
    now = datetime.now(IST)
    samples: list[dict[str, Any]] = []
    for idx, raw_time in enumerate(hourly.get("time", []) or []):
        ts = _parse_open_meteo_time(raw_time)
        if ts is None:
            continue
        rain_mm = _rain_value_mm(hourly, idx)
        samples.append({"time": raw_time, "dt": ts, "rain_mm": rain_mm})

    past_samples = [x for x in samples if x["dt"] <= now]
    current_hour = past_samples[-1] if past_samples else None

    def sum_recent(hours: int) -> float:
        start = now - timedelta(hours=hours)
        return sum(x["rain_mm"] for x in past_samples if start <= x["dt"] <= now)

    current_rain = float(current.get("rain") or current.get("precipitation") or 0)
    current_hour_mm = max(current_rain, float(current_hour["rain_mm"] if current_hour else 0))
    recent_3h = sum_recent(3)
    recent_6h = sum_recent(6)
    recent_12h = sum_recent(12)

    # Convert active rainfall intensity to a daily-equivalent disruption signal.
    # This deliberately does not claim to be measured 24h rainfall; it is a nowcast
    # proxy so the dashboard reacts during heavy rain before daily archive data lands.
    intensity_equivalent = max(
        current_hour_mm * 24,
        recent_3h * 8,
        recent_6h * 4,
        recent_12h * 2,
    )

    return {
        "type": "rain_nowcast",
        "source": "open_meteo_forecast_hourly",
        "observed_at": current.get("time") or (current_hour["time"] if current_hour else None),
        "location": station,
        "value": {
            "current_hour_mm": round(current_hour_mm, 2),
            "recent_3h_mm": round(recent_3h, 2),
            "recent_6h_mm": round(recent_6h, 2),
            "recent_12h_mm": round(recent_12h, 2),
            "intensity_equivalent_mm": round(intensity_equivalent, 2),
            "weather_code": current.get("weather_code"),
            "wind_speed_10m_kmh": current.get("wind_speed_10m"),
        },
        "severity": rainfall_severity(intensity_equivalent),
        "confidence": "medium" if status == "ok" else "low",
    }


def normalize_forecast() -> dict[str, Any]:
    raw = _read_json(f"{RAW_DIR}/open_meteo_forecast.json", [])
    forecasts: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    hourly_observations: list[dict[str, Any]] = []
    nowcast: list[dict[str, Any]] = []

    for station_payload in raw:
        station = station_payload.get("station", {})
        status = station_payload.get("collector_status")
        daily = station_payload.get("daily", {}) or {}
        for idx, day in enumerate(daily.get("time", []) or []):
            precip = float(_value_at(daily.get("precipitation_sum"), idx, 0) or 0)
            forecasts.append({
                "type": "daily_forecast",
                "source": "open_meteo_forecast",
                "forecast_date": day,
                "location": station,
                "value": {
                    "precipitation_sum_mm": precip,
                    "precipitation_probability_max_pct": _value_at(daily.get("precipitation_probability_max"), idx),
                    "weather_code": _value_at(daily.get("weather_code"), idx),
                    "wind_speed_10m_max_kmh": _value_at(daily.get("wind_speed_10m_max"), idx),
                },
                "severity": rainfall_severity(precip),
                "confidence": "medium" if status == "ok" else "low",
            })

        hourly = station_payload.get("hourly") or {}
        for idx, raw_time in enumerate(hourly.get("time", []) or []):
            rain_mm = _rain_value_mm(hourly, idx)
            hourly_observations.append({
                "type": "hourly_rainfall",
                "source": "open_meteo_forecast_hourly",
                "observed_at": raw_time,
                "location": station,
                "value": {
                    "rain_mm": rain_mm,
                    "weather_code": _value_at(hourly.get("weather_code"), idx),
                    "wind_speed_10m_kmh": _value_at(hourly.get("wind_speed_10m"), idx),
                },
                "severity": rainfall_severity(rain_mm * 24),
                "confidence": "medium" if status == "ok" else "low",
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
                "confidence": "medium" if status == "ok" else "low",
            })
        if hourly or cur:
            nowcast.append(_build_station_nowcast(station, hourly, cur, status))

    forecasts.sort(key=lambda x: (x["forecast_date"], x["location"].get("name", "")))
    hourly_observations.sort(key=lambda x: (x["observed_at"] or "", x["location"].get("name", "")))
    payload = {"current": current, "hourly": hourly_observations, "nowcast": nowcast, "daily": forecasts}
    _write_json(f"{NORMALIZED_DIR}/weather_forecast.json", payload)
    return payload


def build_chronological_daily_series(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for obs in observations:
        grouped[obs["observed_date"]].append(obs)

    start = parse_monsoon_start()
    end = today_ist()
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
