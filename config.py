"""Project configuration for Monsoon Dashboard - Mumbai.

The configured Mumbai monsoon start date is 2026-06-02.

This date is intentionally treated as the canonical local project anchor for the
current monsoon chronology. Override MONSOON_START_DATE in the GitHub Actions
environment only if you intentionally want to rebuild the season timeline from
a different date.
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

MONSOON_START_DATE = os.getenv("MONSOON_START_DATE", "2026-06-02")
PROJECT_NAME = "mumbai-monsoon-dashboard"
CITY_NAME = "Mumbai"

DATA_DIR = "data"
RAW_DIR = f"{DATA_DIR}/raw"
NORMALIZED_DIR = f"{DATA_DIR}/normalized"
PUBLIC_DIR = f"{DATA_DIR}/public"
DOCS_DIR = "docs"

OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Expanded Mumbai public-area model.
#
# This is a transparent civic impact model for dashboarding, map visualisation
# and timeline development. It is not an official flood, transport, traffic,
# railway or emergency-response model.
#
# susceptibility:
#   0.30-0.45  lower relative disruption susceptibility
#   0.50-0.65  moderate susceptibility
#   0.70-0.80  high susceptibility
#   0.85-0.95  very high known monsoon-disruption susceptibility
AREAS = [
    # South Mumbai
    {"name": "Colaba", "zone": "South Mumbai", "lat": 18.9067, "lon": 72.8147, "susceptibility": 0.35},
    {"name": "Nariman Point", "zone": "South Mumbai", "lat": 18.9256, "lon": 72.8242, "susceptibility": 0.35},
    {"name": "Churchgate", "zone": "South Mumbai", "lat": 18.9322, "lon": 72.8264, "susceptibility": 0.40},
    {"name": "Marine Lines", "zone": "South Mumbai", "lat": 18.9440, "lon": 72.8236, "susceptibility": 0.45},
    {"name": "CST / Fort", "zone": "South Mumbai", "lat": 18.9398, "lon": 72.8355, "susceptibility": 0.45},
    {"name": "Masjid Bunder", "zone": "South Mumbai", "lat": 18.9518, "lon": 72.8380, "susceptibility": 0.55},
    {"name": "Mumbai Central", "zone": "South Mumbai", "lat": 18.9690, "lon": 72.8205, "susceptibility": 0.55},
    {"name": "Byculla", "zone": "Central Mumbai", "lat": 18.9750, "lon": 72.8333, "susceptibility": 0.60},

    # Central Mumbai
    {"name": "Worli", "zone": "Central Mumbai", "lat": 19.0176, "lon": 72.8162, "susceptibility": 0.55},
    {"name": "Lower Parel", "zone": "Central Mumbai", "lat": 18.9980, "lon": 72.8300, "susceptibility": 0.65},
    {"name": "Prabhadevi", "zone": "Central Mumbai", "lat": 19.0166, "lon": 72.8295, "susceptibility": 0.60},
    {"name": "Parel", "zone": "Central Mumbai", "lat": 18.9930, "lon": 72.8374, "susceptibility": 0.75},
    {"name": "Dadar / Hindmata", "zone": "Central Mumbai", "lat": 19.0206, "lon": 72.8426, "susceptibility": 0.95},
    {"name": "Shivaji Park", "zone": "Central Mumbai", "lat": 19.0280, "lon": 72.8377, "susceptibility": 0.55},
    {"name": "Matunga / King's Circle", "zone": "Central Mumbai", "lat": 19.0270, "lon": 72.8550, "susceptibility": 0.90},
    {"name": "Sion", "zone": "Central Mumbai", "lat": 19.0434, "lon": 72.8633, "susceptibility": 0.85},
    {"name": "Mahim", "zone": "Central Mumbai", "lat": 19.0358, "lon": 72.8426, "susceptibility": 0.70},
    {"name": "Dharavi", "zone": "Central Mumbai", "lat": 19.0380, "lon": 72.8538, "susceptibility": 0.80},

    # Harbour / Eastern corridor
    {"name": "Wadala", "zone": "Harbour / Eastern Corridor", "lat": 19.0178, "lon": 72.8562, "susceptibility": 0.70},
    {"name": "Sewri", "zone": "Harbour / Eastern Corridor", "lat": 18.9986, "lon": 72.8548, "susceptibility": 0.65},
    {"name": "Chunabhatti", "zone": "Harbour / Eastern Corridor", "lat": 19.0522, "lon": 72.8696, "susceptibility": 0.75},
    {"name": "Kurla", "zone": "Central Suburbs", "lat": 19.0726, "lon": 72.8845, "susceptibility": 0.90},
    {"name": "Tilak Nagar", "zone": "Harbour / Eastern Corridor", "lat": 19.0670, "lon": 72.8976, "susceptibility": 0.70},
    {"name": "Chembur", "zone": "Eastern Suburbs", "lat": 19.0522, "lon": 72.9005, "susceptibility": 0.70},
    {"name": "Govandi", "zone": "Harbour / Eastern Corridor", "lat": 19.0556, "lon": 72.9156, "susceptibility": 0.70},
    {"name": "Mankhurd", "zone": "Harbour / Eastern Corridor", "lat": 19.0485, "lon": 72.9322, "susceptibility": 0.70},
    {"name": "Deonar", "zone": "Harbour / Eastern Corridor", "lat": 19.0476, "lon": 72.9129, "susceptibility": 0.65},

    # Western Suburbs
    {"name": "Bandra", "zone": "Western Suburbs", "lat": 19.0607, "lon": 72.8362, "susceptibility": 0.55},
    {"name": "BKC", "zone": "Western Suburbs", "lat": 19.0667, "lon": 72.8679, "susceptibility": 0.65},
    {"name": "Khar", "zone": "Western Suburbs", "lat": 19.0700, "lon": 72.8400, "susceptibility": 0.55},
    {"name": "Santacruz", "zone": "Western Suburbs", "lat": 19.0896, "lon": 72.8656, "susceptibility": 0.65},
    {"name": "Vile Parle", "zone": "Western Suburbs", "lat": 19.1006, "lon": 72.8438, "susceptibility": 0.60},
    {"name": "Juhu", "zone": "Western Suburbs", "lat": 19.1075, "lon": 72.8263, "susceptibility": 0.55},
    {"name": "Andheri West", "zone": "Western Suburbs", "lat": 19.1364, "lon": 72.8296, "susceptibility": 0.65},
    {"name": "Andheri", "zone": "Western Suburbs", "lat": 19.1197, "lon": 72.8464, "susceptibility": 0.65},
    {"name": "Versova", "zone": "Western Suburbs", "lat": 19.1312, "lon": 72.8148, "susceptibility": 0.60},
    {"name": "Lokhandwala / Oshiwara", "zone": "Western Suburbs", "lat": 19.1433, "lon": 72.8244, "susceptibility": 0.65},
    {"name": "Jogeshwari", "zone": "Western Suburbs", "lat": 19.1363, "lon": 72.8487, "susceptibility": 0.70},
    {"name": "Goregaon", "zone": "Western Suburbs", "lat": 19.1663, "lon": 72.8526, "susceptibility": 0.55},
    {"name": "Malad", "zone": "Western Suburbs", "lat": 19.1860, "lon": 72.8485, "susceptibility": 0.60},
    {"name": "Kandivali", "zone": "Western Suburbs", "lat": 19.2045, "lon": 72.8518, "susceptibility": 0.55},
    {"name": "Borivali", "zone": "Western Suburbs", "lat": 19.2307, "lon": 72.8567, "susceptibility": 0.45},
    {"name": "Dahisar", "zone": "Western Suburbs", "lat": 19.2500, "lon": 72.8596, "susceptibility": 0.45},

    # Airport / Andheri East / MIDC corridor
    {"name": "Mumbai Airport / Sahar", "zone": "Airport / MIDC Corridor", "lat": 19.0896, "lon": 72.8656, "susceptibility": 0.65},
    {"name": "Marol", "zone": "Airport / MIDC Corridor", "lat": 19.1191, "lon": 72.8828, "susceptibility": 0.65},
    {"name": "Saki Naka", "zone": "Airport / MIDC Corridor", "lat": 19.1030, "lon": 72.8888, "susceptibility": 0.75},
    {"name": "MIDC Andheri", "zone": "Airport / MIDC Corridor", "lat": 19.1190, "lon": 72.8718, "susceptibility": 0.65},
    {"name": "SEEPZ", "zone": "Airport / MIDC Corridor", "lat": 19.1268, "lon": 72.8746, "susceptibility": 0.60},
    {"name": "Chandivali", "zone": "Airport / MIDC Corridor", "lat": 19.1097, "lon": 72.9003, "susceptibility": 0.65},

    # Eastern Suburbs
    {"name": "Powai", "zone": "Eastern Suburbs", "lat": 19.1176, "lon": 72.9060, "susceptibility": 0.60},
    {"name": "Vidyavihar", "zone": "Eastern Suburbs", "lat": 19.0790, "lon": 72.8970, "susceptibility": 0.65},
    {"name": "Ghatkopar", "zone": "Eastern Suburbs", "lat": 19.0856, "lon": 72.9080, "susceptibility": 0.70},
    {"name": "Vikhroli", "zone": "Eastern Suburbs", "lat": 19.1110, "lon": 72.9280, "susceptibility": 0.55},
    {"name": "Kanjurmarg", "zone": "Eastern Suburbs", "lat": 19.1293, "lon": 72.9330, "susceptibility": 0.55},
    {"name": "Bhandup", "zone": "Eastern Suburbs", "lat": 19.1511, "lon": 72.9372, "susceptibility": 0.55},
    {"name": "Mulund", "zone": "Eastern Suburbs", "lat": 19.1726, "lon": 72.9425, "susceptibility": 0.45},

    # Green / edge zones useful for map context
    {"name": "Aarey", "zone": "Western / Green Zone", "lat": 19.1600, "lon": 72.8830, "susceptibility": 0.45},
    {"name": "Sanjay Gandhi National Park Edge", "zone": "North Mumbai / Green Zone", "lat": 19.2147, "lon": 72.9106, "susceptibility": 0.40},
]


def parse_monsoon_start() -> date:
    return date.fromisoformat(MONSOON_START_DATE)


def today_ist() -> date:
    """Return today's date in Mumbai/IST.

    GitHub Actions runners use UTC by default. The dashboard chronology should
    use Mumbai local dates, especially during monsoon updates around midnight.
    """
    return datetime.now(IST).date()
