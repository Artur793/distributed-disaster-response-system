import requests


BASE_URL = "http://127.0.0.1:8080"


def test_dashboard_serves_static_application_shell():
    response = requests.get(f"{BASE_URL}/dashboard")

    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]
    assert '<div id="map-grid"' in response.text
    assert '<div id="map-y-axis"' in response.text
    assert '<i class="swatch harbor"' in response.text
    assert '<script src="/dashboard.js"' in response.text


def test_dashboard_assets_are_available():
    stylesheet = requests.get(f"{BASE_URL}/dashboard.css")
    script = requests.get(f"{BASE_URL}/dashboard.js")

    assert stylesheet.status_code == 200
    assert "text/css" in stylesheet.headers["Content-Type"]
    assert ".map-grid" in stylesheet.text
    assert "--harbor:" in stylesheet.text
    assert ".x-axis" in stylesheet.text

    assert script.status_code == 200
    assert "application/javascript" in script.headers["Content-Type"]
    assert 'fetch("/status")' in script.text
    assert "setInterval(refreshStatus, 250)" in script.text
    assert "groupByPosition" in script.text


def test_map_data_returns_structured_map_for_live_dashboard():
    response = requests.get(f"{BASE_URL}/map-data")

    assert response.status_code == 200
    assert "application/json" in response.headers["Content-Type"]

    data = response.json()
    assert data["width"] == 20
    assert data["height"] == 20
    assert len(data["cells"]) == data["height"]
    assert len(data["cells"][0]) == data["width"]
    assert data["cells"][0][0]["tile_type"] in ("land", "water")


def test_legacy_map_page_remains_available():
    response = requests.get(f"{BASE_URL}/map")

    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]
    assert "Island Map" in response.text
