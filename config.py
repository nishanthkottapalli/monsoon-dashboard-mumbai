"""Project configuration for Monsoon Dashboard - Mumbai.

The default monsoon start date is set to 2026-06-23 because IMD's 23 June 2026
monsoon advancement note says the Southwest Monsoon advanced into parts of
Maharashtra including Mumbai on that date. Override MONSOON_START_DATE in the
GitHub Actions environment if you want to use a different season anchor.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

@dataclass(frozen=True)
class Station:
    name: str
    latitude: float
    longitude: float
    zone: str

MUMBAI_STATIONS = [
    Station("Colaba", 18.9067, 72.8147, "South Mumbai"),
    Station("Santacruz", 19.0896, 72.8656, "Western Suburbs"),
    Station("Powai", 19.1176, 72.9060, "Eastern Suburbs"),
]

MONSOON_START_DATE = os.getenv("MONSOON_START_DATE", "2026-06-23")
PROJECT_NAME = "mumbai-monsoon-dashboard"
CITY_NAME = "Mumbai"

DATA_DIR = "data"
RAW_DIR = f"{DATA_DIR}/raw"
NORMALIZED_DIR = f"{DATA_DIR}/normalized"
PUBLIC_DIR = f"{DATA_DIR}/public"
DOCS_DIR = "docs"

OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Known monsoon-sensitive public areas. This is a transparent static civic model,
# not an official flood forecast.
AREAS = [
    {"name": "Colaba", "zone": "South Mumbai", "lat": 18.9067, "lon": 72.8147, "susceptibility": 0.35},
    {"name": "CST / Fort", "zone": "South Mumbai", "lat": 18.9398, "lon": 72.8355, "susceptibility": 0.45},
    {"name": "Byculla", "zone": "Central Mumbai", "lat": 18.9750, "lon": 72.8333, "susceptibility": 0.60},
    {"name": "Dadar / Hindmata", "zone": "Central Mumbai", "lat": 19.0206, "lon": 72.8426, "susceptibility": 0.95},
    {"name": "Parel", "zone": "Central Mumbai", "lat": 18.9930, "lon": 72.8374, "susceptibility": 0.75},
    {"name": "Matunga / King's Circle", "zone": "Central Mumbai", "lat": 19.0270, "lon": 72.8550, "susceptibility": 0.90},
    {"name": "Sion", "zone": "Central Mumbai", "lat": 19.0434, "lon": 72.8633, "susceptibility": 0.85},
    {"name": "Kurla", "zone": "Central Suburbs", "lat": 19.0726, "lon": 72.8845, "susceptibility": 0.90},
    {"name": "Chembur", "zone": "Eastern Suburbs", "lat": 19.0522, "lon": 72.9005, "susceptibility": 0.70},
    {"name": "Bandra", "zone": "Western Suburbs", "lat": 19.0607, "lon": 72.8362, "susceptibility": 0.55},
    {"name": "BKC", "zone": "Western Suburbs", "lat": 19.0667, "lon": 72.8679, "susceptibility": 0.65},
    {"name": "Andheri", "zone": "Western Suburbs", "lat": 19.1197, "lon": 72.8464, "susceptibility": 0.65},
    {"name": "Jogeshwari", "zone": "Western Suburbs", "lat": 19.1363, "lon": 72.8487, "susceptibility": 0.70},
    {"name": "Goregaon", "zone": "Western Suburbs", "lat": 19.1663, "lon": 72.8526, "susceptibility": 0.55},
    {"name": "Malad", "zone": "Western Suburbs", "lat": 19.1860, "lon": 72.8485, "susceptibility": 0.60},
    {"name": "Borivali", "zone": "Western Suburbs", "lat": 19.2307, "lon": 72.8567, "susceptibility": 0.45},
    {"name": "Powai", "zone": "Eastern Suburbs", "lat": 19.1176, "lon": 72.9060, "susceptibility": 0.60},
    {"name": "Ghatkopar", "zone": "Eastern Suburbs", "lat": 19.0856, "lon": 72.9080, "susceptibility": 0.70},
    {"name": "Vikhroli", "zone": "Eastern Suburbs", "lat": 19.1110, "lon": 72.9280, "susceptibility": 0.55},
    {"name": "Mulund", "zone": "Eastern Suburbs", "lat": 19.1726, "lon": 72.9425, "susceptibility": 0.45},
]

def parse_monsoon_start() -> date:
    return date.fromisoformat(MONSOON_START_DATE)


def today_ist() -> date:
    """Return today in Mumbai time, not the GitHub runner's UTC date."""
    return datetime.now(IST).date()
