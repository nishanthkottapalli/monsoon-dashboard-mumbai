from __future__ import annotations

import json
import math
import pathlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import RAW_DIR

IST = ZoneInfo("Asia/Kolkata")


def estimate_tide_windows(now: datetime | None = None) -> dict:
    """Generate transparent, non-official tide-risk windows for Mumbai.

    This is not an official tide table. It is a deterministic approximation used
    to create an explainable risk signal for the dashboard when heavy rain and
    high-tide windows overlap. Replace with an official source when available.
    """
    now = now or datetime.now(IST)
    # Semidiurnal tide cycle approximation: 12h 25m.
    cycle_minutes = 12 * 60 + 25
    # Arbitrary phase anchor tuned only to create repeating windows.
    anchor = datetime(2026, 6, 23, 3, 45, tzinfo=IST)
    elapsed = (now - anchor).total_seconds() / 60
    cycles_since_anchor = math.floor(elapsed / cycle_minutes)

    highs = []
    for i in range(-1, 4):
        high_time = anchor + timedelta(minutes=(cycles_since_anchor + i) * cycle_minutes)
        if high_time >= now - timedelta(hours=8):
            highs.append({
                "time": high_time.isoformat(),
                "risk_window_start": (high_time - timedelta(hours=2)).isoformat(),
                "risk_window_end": (high_time + timedelta(hours=2)).isoformat(),
                "confidence": "low",
                "source_type": "computed_estimate",
            })

    payload = {
        "collector_status": "ok",
        "source": "computed_semidiurnal_tide_estimate",
        "generated_at": now.isoformat(),
        "disclaimer": "Approximate non-official tide signal. Use official BMC/Mumbai Port tide tables for safety-critical decisions.",
        "high_tide_windows": highs[:4],
    }
    pathlib.Path(RAW_DIR).mkdir(parents=True, exist_ok=True)
    with open(f"{RAW_DIR}/tide_estimate.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
    return payload


if __name__ == "__main__":
    estimate_tide_windows()
