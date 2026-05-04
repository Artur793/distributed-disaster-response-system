import requests


BASE_URL = "http://127.0.0.1:8080"


def test_register_vehicle_returns_201(unique_id):
    vehicle_id = unique_id("test-drone")

    payload = {
        "id": vehicle_id,
        "unit": "vehicle",
        "vehicle_type": "drone",
        "position": {"x": 2, "y": 3},
    }

    response = requests.post(f"{BASE_URL}/unit", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert data["id"] == vehicle_id
    assert data["vehicle_type"] == "drone"
    assert data["position"] == {"x": 2, "y": 3}
    assert data["status"] == "registered"


def test_register_sensor_returns_201(unique_id):
    sensor_id = unique_id("test-camera")

    payload = {
        "id": sensor_id,
        "unit": "sensor",
        "sensor_type": "camera",
        "position": {"x": 4, "y": 5},
    }

    response = requests.post(f"{BASE_URL}/unit", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert data["id"] == sensor_id
    assert data["sensor_type"] == "camera"
    assert data["position"] == {"x": 4, "y": 5}
    assert data["status"] == "registered"


def test_duplicate_vehicle_registration_returns_409(unique_id):
    vehicle_id = unique_id("test-drone-duplicate")

    payload = {
        "id": vehicle_id,
        "unit": "vehicle",
        "vehicle_type": "drone",
        "position": {"x": 6, "y": 7},
    }

    first = requests.post(f"{BASE_URL}/unit", json=payload)
    second = requests.post(f"{BASE_URL}/unit", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_invalid_json_returns_400():
    response = requests.post(
        f"{BASE_URL}/unit",
        data='{"id":"broken"',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400


def test_missing_vehicle_type_returns_400(unique_id):
    vehicle_id = unique_id("test-drone-missing-type")

    payload = {
        "id": vehicle_id,
        "unit": "vehicle",
        "position": {"x": 1, "y": 1},
    }

    response = requests.post(f"{BASE_URL}/unit", json=payload)

    assert response.status_code == 400
    assert "vehicle_type" in response.text


def test_invalid_unit_type_returns_400(unique_id):
    unit_id = unique_id("test-invalid-unit")

    payload = {
        "id": unit_id,
        "unit": "alien",
        "position": {"x": 1, "y": 1},
    }

    response = requests.post(f"{BASE_URL}/unit", json=payload)

    assert response.status_code == 400