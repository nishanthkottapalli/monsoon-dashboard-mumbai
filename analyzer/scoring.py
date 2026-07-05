from __future__ import annotations

from datetime import datetime
from typing import Any

from config import AREAS, CITY_NAME, IST


def clamp(value: float, low: float = 0, high: float = 100) -> int:
    return int(max(low, min(high, round(value))))


def risk_level(score: float) -> str:
    if score >= 80:
        return "severe"
    if score >= 65:
        return "high"
    if score >= 45:
        return "moderate"
    if score >= 25:
        return "watch"
    return "normal"


def rainfall_score(mm: float) -> int:
    if mm >= 150:
        return 95
    if mm >= 100:
        return 80
    if mm >= 60:
        return 65
    if mm >= 30:
        return 45
    if mm >= 10:
        return 25
    return 10 if mm > 0 else 0


def weather_alert_score(max_rain_mm: float) -> int:
    # Open data does not provide authoritative IMD colour warnings here. This is
    # a rainfall-derived alert proxy used only for the explainable public score.
    if max_rain_mm >= 150:
        return 90
    if max_rain_mm >= 100:
        return 75
    if max_rain_mm >= 60:
        return 60
    if max_rain_mm >= 30:
        return 35
    return 10


def waterlogging_score(max_rain_mm: float) -> int:
    if max_rain_mm >= 150:
        return 90
    if max_rain_mm >= 100:
        return 75
    if max_rain_mm >= 60:
        return 60
    if max_rain_mm >= 30:
        return 40
    return 10


def traffic_score(max_rain_mm: float) -> int:
    if max_rain_mm >= 150:
        return 85
    if max_rain_mm >= 100:
        return 70
    if max_rain_mm >= 60:
        return 55
    if max_rain_mm >= 30:
        return 35
    return 10


def rail_score(max_rain_mm: float) -> int:
    if max_rain_mm >= 150:
        return 80
    if max_rain_mm >= 100:
        return 65
    if max_rain_mm >= 60:
        return 45
    if max_rain_mm >= 30:
        return 25
    return 5


def tide_score(max_rain_mm: float, tide_signal: dict[str, Any]) -> int:
    if max_rain_mm < 60:
        return 10
    windows = tide_signal.get("high_tide_windows") or []
    if not windows:
        return 20
    # Estimate higher risk when there is heavy rain and a known upcoming tide window.
    return 75 if max_rain_mm >= 100 else 45


def city_impact_score(max_rain_mm: float, tide_signal: dict[str, Any]) -> dict[str, Any]:
    scores = {
        "rainfall": rainfall_score(max_rain_mm),
        "weather_alert": weather_alert_score(max_rain_mm),
        "waterlogging": waterlogging_score(max_rain_mm),
        "traffic": traffic_score(max_rain_mm),
        "rail": rail_score(max_rain_mm),
        "tide": tide_score(max_rain_mm, tide_signal),
    }
    weighted = (
        scores["rainfall"] * 0.30
        + scores["weather_alert"] * 0.20
        + scores["waterlogging"] * 0.20
        + scores["traffic"] * 0.15
        + scores["rail"] * 0.10
        + scores["tide"] * 0.05
    )
    final = clamp(weighted)
    return {
        "name": CITY_NAME,
        "impact_score": final,
        "risk_level": risk_level(final),
        "driver_scores": scores,
    }


def score_area(area: dict[str, Any], max_rain_mm: float, city_score: int) -> dict[str, Any]:
    local = city_score * 0.70 + rainfall_score(max_rain_mm) * 0.20 + (area["susceptibility"] * 100) * 0.10
    score = clamp(local)
    signals = ["rainfall"]
    if max_rain_mm >= 30:
        signals.append("traffic")
    if max_rain_mm >= 60 and area["susceptibility"] >= 0.60:
        signals.append("waterlogging")
    if max_rain_mm >= 100:
        signals.append("rail")
    return {
        "name": area["name"],
        "zone": area["zone"],
        "lat": area["lat"],
        "lon": area["lon"],
        "susceptibility": area["susceptibility"],
        "impact_score": score,
        "risk_level": risk_level(score),
        "signals": signals,
        "summary": area_summary(area, score, max_rain_mm),
    }


def area_summary(area: dict[str, Any], score: int, max_rain_mm: float) -> str:
    level = risk_level(score)
    if level in {"high", "severe"}:
        return f"Elevated monsoon disruption risk in {area['name']} due to rainfall intensity and known local susceptibility. Check official advisories before travel."
    if level == "moderate":
        return f"Moderate monsoon impact risk in {area['name']}; expect slower movement during rain bands."
    if level == "watch":
        return f"Watch conditions in {area['name']}; disruption may rise if rainfall intensifies."
    return f"Normal to low disruption signal for {area['name']} based on the current public data model."


def build_area_scores(max_rain_mm: float, city_score: int) -> list[dict[str, Any]]:
    areas = [score_area(area, max_rain_mm, city_score) for area in AREAS]
    areas.sort(key=lambda x: (-x["impact_score"], x["name"]))
    return areas


def build_briefing(city: dict[str, Any], max_rain_mm: float) -> dict[str, Any]:
    level = city["risk_level"]
    if level == "severe":
        headline = "Mumbai is facing severe monsoon disruption risk."
    elif level == "high":
        headline = "Mumbai is facing high monsoon disruption risk."
    elif level == "moderate":
        headline = "Mumbai is under moderate monsoon watch."
    elif level == "watch":
        headline = "Mumbai has early monsoon disruption signals."
    else:
        headline = "Mumbai monsoon disruption signal is currently low."

    advisory = [
        "Use official IMD, BMC, Mumbai Police, railway and airport advisories for safety-critical decisions.",
        "Avoid low-lying areas during intense rain and near high-tide overlap windows.",
        "Allow additional time for road and rail journeys during active rain bands.",
    ]
    if max_rain_mm >= 60:
        advisory.insert(1, "Expect localised waterlogging and slower transport movement in susceptible areas.")

    return {
        "headline": headline,
        "overview": f"The current explainable model is driven primarily by a maximum observed/forecast rainfall signal of {round(max_rain_mm, 1)} mm.",
        "public_advisory": advisory,
        "method_note": "Impact is computed from public rainfall data plus transparent derived signals for waterlogging, traffic, rail and tide risk. This is not an official alerting system.",
    }
