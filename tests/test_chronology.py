from analyzer.build import merge_chronology
from normalizers.weather import build_chronological_daily_series


def test_chronology_is_sorted(monkeypatch):
    observations = [
        {"observed_date": "2026-06-24", "location": {"name": "A"}, "value": {"precipitation_sum_mm": 2}},
        {"observed_date": "2026-06-23", "location": {"name": "A"}, "value": {"precipitation_sum_mm": 1}},
    ]
    series = build_chronological_daily_series(observations)
    dates = [row["date"] for row in series]
    assert dates == sorted(dates)
    assert dates[0] == "2026-06-23"


def test_chronology_merge_replaces_by_date_and_preserves_order():
    existing = [
        {"date": "2026-06-23", "rainfall_mm_max": 1},
        {"date": "2026-06-25", "rainfall_mm_max": 3},
    ]
    incoming = [
        {"date": "2026-06-24", "rainfall_mm_max": 2},
        {"date": "2026-06-25", "rainfall_mm_max": 4},
    ]
    merged = merge_chronology(existing, incoming)
    assert [row["date"] for row in merged] == ["2026-06-23", "2026-06-24", "2026-06-25"]
    assert merged[-1]["rainfall_mm_max"] == 4
