from analyzer.scoring import rainfall_score, risk_level, city_impact_score


def test_rainfall_score_bands():
    assert rainfall_score(0) == 0
    assert rainfall_score(15) == 25
    assert rainfall_score(75) == 65
    assert rainfall_score(125) == 80
    assert rainfall_score(175) == 95


def test_risk_level_bands():
    assert risk_level(10) == "normal"
    assert risk_level(30) == "watch"
    assert risk_level(50) == "moderate"
    assert risk_level(70) == "high"
    assert risk_level(90) == "severe"


def test_city_score_shape():
    payload = city_impact_score(120, {"high_tide_windows": [{"time": "x"}]})
    assert payload["name"] == "Mumbai"
    assert 0 <= payload["impact_score"] <= 100
    assert "rainfall" in payload["driver_scores"]
