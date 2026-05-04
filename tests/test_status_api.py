import requests


BASE_URL = "http://127.0.0.1:8080"


def test_get_status_returns_200_and_json():
    response = requests.get(f"{BASE_URL}/status")

    assert response.status_code == 200
    data = response.json()

    assert "map_loaded" in data
    assert "vehicle_count" in data
    assert "sensor_count" in data
    assert "incident_count" in data
    assert "vehicles" in data
    assert "sensors" in data
    assert "incidents" in data


def test_get_map_returns_expected_status():
    response = requests.get(f"{BASE_URL}/map")

    assert response.status_code in (200, 404)

    if response.status_code == 404:
        assert response.text == "Map not initialized"


def test_post_status_not_allowed():
    response = requests.post(f"{BASE_URL}/status")

    assert response.status_code == 405


def test_unknown_route_returns_404():
    response = requests.get(f"{BASE_URL}/does-not-exist")

    assert response.status_code == 404