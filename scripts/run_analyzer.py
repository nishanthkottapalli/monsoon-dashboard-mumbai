from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_normalizers import main as normalize
from analyzer.build import update_chronology_payload


def main() -> None:
    normalize()
    update_chronology_payload(require_chronology=True)


if __name__ == "__main__":
    main()
