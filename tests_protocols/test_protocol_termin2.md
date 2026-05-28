# Test_Termin2 Report — DoY5BlockTeamF

## Project Overview


The purpose of these tests is to verify:

- Functional correctness of REST API endpoints
- Validation and error handling
- Registration and incident workflows
- System stability
- Performance and latency behavior under load

---


# Test Execution

## Diploy all the Containers

```bash
docker compose up
```

## Run All Tests

```bash
pytest -v
```

---

# Test Summary

| Test Category | Test Count | Passed | Failed |
|---|---|---|---|
| Incident API Tests | 5 | 5 | 0 |
| Latency & Performance Tests | 6 | 6 | 0 |
| Status API Tests | 4 | 4 | 0 |
| Unit Registration Tests | 7 | 7 | 0 |
| TOTAL | 22 | 22 | 0 |

---

# Functional Tests

Functional tests verify that the API behaves according to the specification.

---

# 1. Incident API Tests

File:
```text
tests/test_incident.py
```

## Objective

Verify incident management functionality.

The tests validate:

- Successful incident creation
- Validation of source IDs
- Duplicate incident prevention

---

## Tested Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/incident` | POST | Create incident |
| `/unit` | POST | Register source sensor |

---

## Test Cases

| Test Name | Description | Expected Result |
|---|---|---|
| `test_create_incident_with_known_source_returns_201` | Create incident using registered sensor | HTTP 201 |
| `test_create_incident_with_unknown_source_returns_400` | Reject unknown source ID | HTTP 400 |
| `test_duplicate_incident_returns_409` | Reject duplicate incident IDs | HTTP 409 |
| `test_create_incident_without_position_returns_400` | Reject duplicate incident IDs | HTTP 400 |
| `test_create_incident_outside_map_returns_400` | Reject incident outside the map | HTTP 400 |

---

## Example Test Code

```python
def test_duplicate_incident_returns_409(unique_id):
    source_id = unique_id("incident-source-water")
    incident_id = unique_id("incident-duplicate")

    sensor_payload = {
        "id": source_id,
        "unit": "sensor",
        "sensor_type": "water",
        "position": {"x": 7, "y": 8},
    }

    requests.post(f"{BASE_URL}/unit", json=sensor_payload)

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
```

---

# 2. Status API Tests

File:
```text
tests/test_status.py
```

## Objective

Verify system monitoring and status endpoints.

The tests validate:

- Availability of system status information
- Correct HTTP methods
- Proper error handling for invalid routes

---

## Tested Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/status` | GET | System status |
| `/status` | POST | Method validation |
| `/map` | GET | Map information |
| Invalid routes | GET | 404 handling |

---

## Test Cases

| Test Name | Description | Expected Result |
|---|---|---|
| `test_get_status_returns_200_and_json` | Verify valid status response | HTTP 200 |
| `test_get_map_returns_expected_status` | Verify map behavior | HTTP 200 or 404 |
| `test_post_status_not_allowed` | Verify method restriction | HTTP 405 |
| `test_unknown_route_returns_404` | Verify unknown route handling | HTTP 404 |

---

## Verified JSON Fields

The `/status` endpoint response is validated for the following fields:

- `map_loaded`
- `vehicle_count`
- `sensor_count`
- `incident_count`
- `vehicles`
- `sensors`
- `incidents`

---

# 3. Unit Registration Tests

File:
```text
tests/test_unit.py
```

## Objective

Verify vehicle and sensor registration functionality.

The tests validate:

- Vehicle registration
- Sensor registration
- Duplicate prevention
- Input validation
- Error handling

---

## Tested Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/unit` | POST | Register vehicles and sensors |

---

## Test Cases

| Test Name | Description | Expected Result |
|---|---|---|
| `test_register_vehicle_returns_201` | Register vehicle | HTTP 201 |
| `test_register_sensor_returns_201` | Register sensor | HTTP 201 |
| `test_duplicate_vehicle_registration_returns_409` | Reject duplicate ID | HTTP 409 |
| `test_invalid_json_returns_400` | Reject malformed JSON | HTTP 400 |
| `test_missing_vehicle_type_returns_400` | Validate required fields | HTTP 400 |
| `test_missing_vehicle_rpc_endpoint_returns_400` | reject invalid vahicle in rpc | HTTP 400 |
| `test_invalid_unit_type_returns_400` | Reject invalid unit type | HTTP 400 |

---

## Example Test Code

```python
def test_invalid_json_returns_400():
    response = requests.post(
        f"{BASE_URL}/unit",
        data='{"id":"broken"',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
```

---

# Non-Functional Tests

Non-functional tests verify system performance and stability.

---

# 4. Latency & Performance Tests

File:
```text
tests/test_latency.py
```

## Objective

Measure API response times and behavior under concurrent load.

The tests evaluate:

- Endpoint latency
- Average response times
- Concurrent request handling
- Burst traffic stability

---

## Tested Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/status` | GET | Status performance |
| `/incident` | POST | Incident performance |

---

## Performance Targets

| Metric | Target |
|---|---|
| GET latency | < 100 ms |
| POST latency | < 100 ms |
| Concurrent handling | Stable |
| Burst handling | Stable |

---

## Measured Results

| Test | Measured Result |
|---|---|
| GET `/status` latency | 0.22 ms |
| Average GET latency | 0.17 ms |
| POST `/incident` latency | 0.18 ms |
| Average POST latency | 0.18 ms |
| Concurrent average latency | 0.59 ms |
| Concurrent maximum latency | 0.72 ms |
| Burst median latency | 0.25 ms |
| Burst 99th percentile | 0.28 ms |

---

## Concurrency Test

The concurrency test creates multiple parallel threads:

```python
threads = [threading.Thread(target=worker) for _ in range(10)]
```

This verifies that the server can process simultaneous requests without significant degradation.

---

## Burst Test

The burst test rapidly sends 50 consecutive requests to evaluate short-term stability and response consistency.

---

# Test Architecture

## Testing Framework

The project uses:

- `pytest` for test execution
- `requests` for HTTP API communication
- `socket` for low-level latency testing
- `threading` for concurrency simulation

---

# Test Data Strategy

Unique IDs are generated dynamically using the `unique_id` fixture to avoid conflicts between test executions.

Example:

```python
vehicle_id = unique_id("test-drone")
```

This ensures:

- test independence
- repeatable execution
- no database collisions

---

# Error Handling Validation

The following error conditions are tested:

| Error Scenario | Expected HTTP Code |
|---|---|
| Unknown source ID | 400 |
| Invalid JSON | 400 |
| Invalid unit type | 400 |
| Duplicate IDs | 409 |
| Unsupported method | 405 |
| Unknown route | 404 |

---


# Conclusion

All automated tests passed successfully.

The system fulfills the tested requirements regarding:

- API correctness
- Validation behavior
- Error handling
- Registration workflows
- Incident management
- Response performance
- Concurrent request handling

Final Result:

```text
22 passed in 0.33s
```


