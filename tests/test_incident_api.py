import requests


BASE_URL = "http://127.0.0.1:8080"


def test_create_incident_with_known_source_returns_201(unique_id):
    source_id = unique_id("incident-source-camera")
    incident_id = unique_id("incident")

    sensor_payload = {
        "id": source_id,
        "unit": "sensor",
        "sensor_type": "camera",
        "position": {"x": 10, "y": 12},
    }

    register_response = requests.post(f"{BASE_URL}/unit", json=sensor_payload)
    assert register_response.status_code == 201

    incident_payload = {
        "id": incident_id,
        "incident_type": "person_detected",
        "source_id": source_id,
        "message": "Person near bridge",
        "position": {"x": 10, "y": 12},
        "priority": 2,
    }

    response = requests.post(f"{BASE_URL}/incident", json=incident_payload)

    assert response.status_code == 201
    data = response.json()

    assert data["id"] == incident_id
    assert data["source_id"] == source_id
    assert data["message"] == "Person near bridge"


def test_create_incident_with_unknown_source_returns_400(unique_id):
    incident_id = unique_id("incident-unknown-source")

    payload = {
        "id": incident_id,
        "incident_type": "person_detected",
        "source_id": "does-not-exist",
        "message": "Should fail",
        "position": {"x": 1, "y": 1},
    }

    response = requests.post(f"{BASE_URL}/incident", json=payload)

    assert response.status_code == 400
    assert "Unknown source_id" in response.text


def test_duplicate_incident_returns_409(unique_id):
    source_id = unique_id("incident-source-water")
    incident_id = unique_id("incident-duplicate")

    sensor_payload = {
        "id": source_id,
        "unit": "sensor",
        "sensor_type": "water",
        "position": {"x": 7, "y": 8},
    }

    register_response = requests.post(f"{BASE_URL}/unit", json=sensor_payload)
    assert register_response.status_code == 201

    incident_payload = {
        "id": incident_id,
        "incident_type": "water_level_alert",
        "source_id": source_id,
        "message": "Water too high",
        "position": {"x": 7, "y": 8},
    }

    first = requests.post(f"{BASE_URL}/incident", json=incident_payload)
    second = requests.post(f"{BASE_URL}/incident", json=incident_payload)

    assert first.status_code == 201
    assert second.status_code == 409