from __future__ import annotations

import json
import pathlib
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collectors.open_meteo import collect_archive, collect_forecast
from collectors.tide_estimate import estimate_tide_windows
from normalizers.weather import normalize_archive, normalize_forecast, build_chronological_daily_series
from normalizers.tide import normalize_tide
from analyzer.build import seed_chronology_payload
from config import NORMALIZED_DIR


def main() -> None:
    """Seed data/public/chronology.json from monsoon start to today.

    Intended to be run manually before the scheduled update workflow is enabled.
    """
    collect_archive()
    collect_forecast()
    estimate_tide_windows()
    observations = normalize_archive()
    normalize_forecast()
    daily = build_chronological_daily_series(observations)
    pathlib.Path(NORMALIZED_DIR).mkdir(parents=True, exist_ok=True)
    with open(f"{NORMALIZED_DIR}/daily_weather_series.json", "w", encoding="utf-8") as f:
        json.dump(daily, f, ensure_ascii=False, indent=2, sort_keys=True)
    tide_signal = normalize_tide()
    seed_chronology_payload(daily, tide_signal)


if __name__ == "__main__":
    main()
