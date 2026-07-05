from __future__ import annotations

import json
import pathlib
from typing import Any

from config import NORMALIZED_DIR, RAW_DIR


def normalize_tide() -> dict[str, Any]:
    try:
        with open(f"{RAW_DIR}/tide_estimate.json", "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        raw = {"collector_status": "missing", "high_tide_windows": []}

    payload = {
        "type": "tide_signal",
        "source": raw.get("source", "computed_semidiurnal_tide_estimate"),
        "generated_at": raw.get("generated_at"),
        "confidence": "low",
        "disclaimer": raw.get("disclaimer"),
        "high_tide_windows": raw.get("high_tide_windows", []),
    }
    pathlib.Path(NORMALIZED_DIR).mkdir(parents=True, exist_ok=True)
    with open(f"{NORMALIZED_DIR}/tide_signal.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
    return payload


if __name__ == "__main__":
    normalize_tide()
