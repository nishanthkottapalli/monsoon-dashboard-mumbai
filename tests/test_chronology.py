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


def test_today_nowcast_updates_chronology_row(monkeypatch):
    import analyzer.build as build

    class FakeDate:
        def isoformat(self):
            return "2026-07-05"

    monkeypatch.setattr(build, "today_ist", lambda: FakeDate())
    chronology = [
        {"date": "2026-07-04", "rainfall_mm_max": 10, "impact_score": 25, "risk_level": "watch"},
        {"date": "2026-07-05", "rainfall_mm_max": 0, "impact_score": 0, "risk_level": "normal"},
    ]
    signal = {"value_mm": 180, "basis": "nowcast_intensity_equivalent_mm"}
    updated = build.apply_today_nowcast_to_chronology(chronology, signal, {"high_tide_windows": []})
    assert [row["date"] for row in updated] == ["2026-07-04", "2026-07-05"]
    assert updated[-1]["rainfall_mm_max"] == 180
    assert updated[-1]["provisional"] is True
    assert updated[-1]["risk_level"] in {"high", "severe"}
