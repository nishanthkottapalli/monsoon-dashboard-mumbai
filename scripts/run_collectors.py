from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collectors.open_meteo import collect_archive, collect_forecast
from collectors.tide_estimate import estimate_tide_windows


def main() -> None:
    collect_archive()
    collect_forecast()
    estimate_tide_windows()


if __name__ == "__main__":
    main()
