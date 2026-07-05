from __future__ import annotations

import json
import pathlib
from datetime import date, datetime
from typing import Any

from config import NORMALIZED_DIR, PUBLIC_DIR, IST, parse_monsoon_start
from analyzer.scoring import build_area_scores, build_briefing, city_impact_score, risk_level

CHRONOLOGY_FILENAME = "chronology.json"
CHRONOLOGY_PATH = f"{PUBLIC_DIR}/{CHRONOLOGY_FILENAME}"


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


def latest_rainfall_signal(daily_series: list[dict[str, Any]], forecast: dict[str, Any]) -> float:
    """Pick the best current rainfall signal available.

    Prefer today's archive/forecast values. If the API has not published today's
    archive yet, fall back to the last chronological history row.
    """
    today = date.today().isoformat()
    values: list[float] = []
    for row in daily_series:
        if row["date"] >= today:
            values.append(float(row.get("rainfall_mm_max") or 0))
    for row in forecast.get("daily", []):
        if row.get("forecast_date") == today:
            values.append(float(row.get("value", {}).get("precipitation_sum_mm") or 0))
    if not values and daily_series:
        values.append(float(daily_series[-1].get("rainfall_mm_max") or 0))
    return max(values) if values else 0.0


def enrich_chronology_rows(daily_series: list[dict[str, Any]], tide_signal: dict[str, Any]) -> list[dict[str, Any]]:
    """Return one strictly chronological row per date."""
    chronological: list[dict[str, Any]] = []
    seen_dates: set[str] = set()
    for row in sorted(daily_series, key=lambda x: x["date"]):
        row_date = row["date"]
        if row_date in seen_dates:
            continue
        seen_dates.add(row_date)
        mm = float(row.get("rainfall_mm_max") or 0)
        city = city_impact_score(mm, tide_signal)
        chronological.append({
            "date": row_date,
            "rainfall_mm_max": round(mm, 2),
            "rainfall_mm_avg": row.get("rainfall_mm_avg", 0),
            "impact_score": city["impact_score"],
            "risk_level": city["risk_level"],
            "severity": row.get("severity"),
        })
    return chronological


def merge_chronology(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge by date and return strictly chronological rows.

    Incoming rows replace existing rows for the same date so late corrections to
    recent archive values do not disturb the timeline order.
    """
    by_date: dict[str, dict[str, Any]] = {}
    for row in existing + incoming:
        row_date = row.get("date")
        if row_date:
            by_date[str(row_date)] = row
    return [by_date[key] for key in sorted(by_date)]


def _collector_statuses() -> list[dict[str, Any]]:
    statuses = []
    for filename, label in [
        ("open_meteo_archive.json", "Open-Meteo archive collector"),
        ("open_meteo_forecast.json", "Open-Meteo forecast collector"),
        ("tide_estimate.json", "Tide estimate collector"),
    ]:
        raw = _read_json(f"data/raw/{filename}", None)
        if raw is None:
            statuses.append({"name": label, "status": "missing", "error": None})
            continue
        if isinstance(raw, list):
            errors = [x.get("error") for x in raw if isinstance(x, dict) and x.get("collector_status") != "ok"]
            statuses.append({"name": label, "status": "error" if errors else "ok", "error": errors[0] if errors else None})
        else:
            statuses.append({"name": label, "status": raw.get("collector_status", "ok"), "error": raw.get("error")})
    return statuses


def _existing_chronology_rows() -> list[dict[str, Any]]:
    existing_payload = _read_json(CHRONOLOGY_PATH, {})
    if isinstance(existing_payload, dict):
        rows = existing_payload.get("chronology", [])
        return rows if isinstance(rows, list) else []
    if isinstance(existing_payload, list):
        # Backward compatibility for early experiments that wrote a bare array.
        return existing_payload
    return []


def _compose_chronology_payload(
    chronology_rows: list[dict[str, Any]],
    max_rain_mm: float,
    tide_signal: dict[str, Any],
    forecast: dict[str, Any],
) -> dict[str, Any]:
    city = city_impact_score(max_rain_mm, tide_signal)
    areas = build_area_scores(max_rain_mm, city["impact_score"])
    briefing = build_briefing(city, max_rain_mm)
    return {
        "project": "mumbai-monsoon-dashboard",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(IST).isoformat(),
        "monsoon_start_date": parse_monsoon_start().isoformat(),
        "chronology": chronology_rows,
        "current": {
            "city": {
                **city,
                "summary": briefing["headline"],
            },
            "drivers": {
                name: {
                    "score": score,
                    "level": risk_level(score),
                    "confidence": "medium" if name in {"rainfall", "weather_alert"} else "low" if name == "tide" else "derived",
                }
                for name, score in city["driver_scores"].items()
            },
            "rainfall_signal_mm": round(max_rain_mm, 2),
            "areas": areas,
            "briefing": briefing,
            "tide": tide_signal,
            "forecast": forecast,
        },
        "collector_statuses": _collector_statuses(),
        "sources": [
            {
                "name": "Open-Meteo Historical Weather API",
                "type": "rainfall_history",
                "confidence": "medium",
                "notes": "No-key public historical weather API. Used for chronological monsoon-season rainfall series.",
            },
            {
                "name": "Open-Meteo Forecast API",
                "type": "current_forecast_weather",
                "confidence": "medium",
                "notes": "No-key public weather forecast API. Used for current rainfall signal and forecast cards.",
            },
            {
                "name": "Computed tide estimate",
                "type": "tide_risk_proxy",
                "confidence": "low",
                "notes": "Transparent non-official tide estimate. Replace with official tide data if available.",
            },
        ],
        "disclaimer": "Experimental public-information dashboard. Not an official emergency, disaster-management, weather, traffic, railway or airport system.",
    }


def seed_chronology_payload(
    daily_series: list[dict[str, Any]] | None = None,
    tide_signal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create data/public/chronology.json from monsoon start onward.

    This is intended for the manual seed workflow. It does not require a
    pre-existing chronology file. Output rows are date-ascending.
    """
    daily_series = daily_series if daily_series is not None else _read_json(f"{NORMALIZED_DIR}/daily_weather_series.json", [])
    tide_signal = tide_signal if tide_signal is not None else _read_json(f"{NORMALIZED_DIR}/tide_signal.json", {"high_tide_windows": []})
    forecast = _read_json(f"{NORMALIZED_DIR}/weather_forecast.json", {"daily": [], "current": []})
    chronology = enrich_chronology_rows(daily_series, tide_signal)
    max_rain_mm = latest_rainfall_signal(daily_series, forecast)
    payload = _compose_chronology_payload(chronology, max_rain_mm, tide_signal, forecast)
    _write_json(CHRONOLOGY_PATH, payload)
    return payload


def update_chronology_payload(require_chronology: bool = True) -> dict[str, Any]:
    """Update the canonical chronology.json file.

    The scheduled/latest workflow should call this with require_chronology=True
    so it cannot run before the manual seed job has created chronology.json.
    """
    chronology_path = pathlib.Path(CHRONOLOGY_PATH)
    if require_chronology and not chronology_path.exists():
        raise FileNotFoundError(
            "data/public/chronology.json does not exist. Run the manual Seed Monsoon Chronology workflow before scheduled updates."
        )

    existing_rows = _existing_chronology_rows()
    daily_series = _read_json(f"{NORMALIZED_DIR}/daily_weather_series.json", [])
    forecast = _read_json(f"{NORMALIZED_DIR}/weather_forecast.json", {"daily": [], "current": []})
    tide_signal = _read_json(f"{NORMALIZED_DIR}/tide_signal.json", {"high_tide_windows": []})
    incoming_rows = enrich_chronology_rows(daily_series, tide_signal)
    chronology = merge_chronology(existing_rows, incoming_rows)
    max_rain_mm = latest_rainfall_signal(daily_series, forecast)
    payload = _compose_chronology_payload(chronology, max_rain_mm, tide_signal, forecast)
    _write_json(CHRONOLOGY_PATH, payload)
    return payload


# Backward-compatible aliases for older local commands.
build_history_payload = seed_chronology_payload
build_public_payload = update_chronology_payload


if __name__ == "__main__":
    update_chronology_payload()
