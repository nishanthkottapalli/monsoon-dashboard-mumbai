from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import pathlib
import shutil
from typing import Any

from config import AREAS, DOCS_DIR, PUBLIC_DIR


def _write_json(path: str, payload: Any) -> None:
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)


def build_geojson() -> dict[str, Any]:
    features = []
    for area in AREAS:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [area["lon"], area["lat"]]},
            "properties": {k: v for k, v in area.items() if k not in {"lat", "lon"}},
        })
    geojson = {"type": "FeatureCollection", "features": features}
    _write_json(f"{PUBLIC_DIR}/areas.geojson", geojson)
    return geojson


def copy_dashboard_to_docs() -> None:
    pathlib.Path(DOCS_DIR).mkdir(parents=True, exist_ok=True)
    for filename in ["index.html", "app.js", "styles.css"]:
        shutil.copyfile(f"dashboard/{filename}", f"{DOCS_DIR}/{filename}")
    pathlib.Path(f"{DOCS_DIR}/data").mkdir(parents=True, exist_ok=True)
    for filename in ["chronology.json", "areas.geojson"]:
        src = f"{PUBLIC_DIR}/{filename}"
        if pathlib.Path(src).exists():
            shutil.copyfile(src, f"{DOCS_DIR}/data/{filename}")


def main() -> None:
    build_geojson()
    copy_dashboard_to_docs()


if __name__ == "__main__":
    main()
