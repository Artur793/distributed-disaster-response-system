# Aufgabe 3 - MQTT Integration Contract

## Purpose

This document defines the MQTT-related architecture and integration decisions introduced in Aufgabe 3. All components must follow these contracts to ensure compatibility.

---

# 1. MQTT Broker

## Selected Broker

Mosquitto

## Reasoning

* Lightweight and easy to deploy
* Official Docker image available
* Satisfies all assignment requirements
* Minimal configuration effort
* Widely used in educational and IoT environments

## Deployment

The broker runs as its own Docker container.

---

# 2. Debugging and Testing Tools

## Primary Tool

MQTT Explorer

Used for:

* Topic inspection
* Message inspection
* QoS verification
* Debugging publishers and subscribers

## Optional Tool

Postman

May be used for:

* Manual MQTT publishing
* Manual MQTT subscriptions
* Testing message formats

Postman is not part of the deployed system and is only used for development and testing.

---

# 3. Topic Structure

## Incident Events

Pattern:

```text
island/events/{source_type}/{source_id}
```

Examples:

```text
island/events/sensor/water-1
island/events/sensor/vibration-1
island/events/camera/camera-1
```

---

## Vehicle Telemetry

Pattern:

```text
island/telemetry/{vehicle_id}
```

Examples:

```text
island/telemetry/drone-1
island/telemetry/rover-1
island/telemetry/boat-1
```

---

## Vehicle Status

Pattern:

```text
island/status/{vehicle_id}
```

Examples:

```text
island/status/drone-1
island/status/rover-1
island/status/boat-1
```

---

# 4. Message Format

All MQTT messages use JSON.

The exact schema may evolve during implementation, but every message should contain at least the common envelope fields:

```json
{
  "version": "1.0",
  "message_id": "msg-001",
  "timestamp": "2026-06-08T18:00:00Z"
}
```

Incident messages identify their publisher with `source_id`.
Vehicle messages identify their publisher with `vehicle_id`.

---

## Example Incident Event

```json
{
  "version": "1.0",
  "message_id": "msg-002",
  "timestamp": "2026-06-08T18:00:00Z",
  "id": "camera-1-incident-{incident_counter}",
  "incident_type": "person_detected",
  "source_id": "camera-1",
  "message": "Person Detected with High-Probability: {person_confidence}",
  "position": {
     "x": 6,
     "y": 10
  },
  "priority": 1,
  "status": "open"
}
```

---

## Example Vehicle Telemetry

```json
{
  "version": "1.0",
  "message_id": "msg-010",
  "timestamp": "2026-06-08T18:00:00Z",
  "vehicle_id": "drone-1",
  "position": {
    "x": 6,
    "y": 9
  },
  "state": "BUSY",
  "assigned_mission_id": "incident-1",
  "progress_percent": 50,
  "result": null
}
```

---

# 5. Event Definitions

The following sensor thresholds generate incidents:

| Sensor Value     | Condition | Generated Event   |
| ---------------- | --------- | ----------------- |
| water_level_cm   | > 80      | water_level_alert |
| person_confidence | > 80     | person_detected   |
| vibration_index  | > 80      | vibration_alert   |

---

# 6. QoS Policy

## Incident Events

QoS: 1

### Reasoning

Incident events must arrive reliably.

QoS 1 guarantees "at least once" delivery. Duplicate messages are acceptable because duplicate handling is already implemented by the Leitstelle and explicitly required by the assignment.

QoS 2 was not selected because it introduces additional protocol overhead while not eliminating the need for application-level duplicate handling.

---

## Vehicle Telemetry

QoS: 0

### Reasoning

Telemetry updates are published frequently.

Losing an occasional position update is acceptable because newer updates will follow shortly.

---

## Vehicle Status

QoS: 1

### Reasoning

Status changes (e.g. IDLE, BUSY, ERROR) should be delivered reliably.

---

# 7. Duplicate Handling

The Leitstelle is responsible for duplicate detection.

## Message-Level Duplicates

If a received message contains a message_id that has already been processed:

```text
Ignore message
```

---

## Incident-Level Duplicates

If two incidents have:

* identical event type
* identical position

within a short time window (implementation-defined)

they should be treated as the same incident.

---

# 8. Old Message Handling

Every MQTT message contains a timestamp.

Messages that are older than the accepted threshold should be ignored by the Leitstelle.

Initial threshold:

```text
60 seconds
```

This value may be adjusted during implementation.

---

# 9. MQTT Retained Messages

Retained messages are disabled.

Reason:

The system should reflect the current runtime state and avoid replaying outdated incidents after reconnects.

---

# 10. MQTT Last Will and Testament (LWT)

Vehicle clients should configure a Last Will and Testament message using an existing vehicle state.

Example:

Topic:

```text
island/status/drone-1
```

Payload:

```json
{
  "version": "1.0",
  "message_id": "msg-lwt-drone-1",
  "timestamp": "2026-06-08T18:00:00Z",
  "vehicle_id": "drone-1",
  "status": "ERROR",
  "result": "Unexpected MQTT disconnect"
}
```

This allows unexpected disconnects to be detected automatically without adding a new vehicle status to the current model.

---

# 11. Reconnection Policy

All MQTT clients should automatically reconnect after connection loss.

Initial reconnect interval:

```text
5 seconds
```

This supports broker restart and failure testing.

---

# 12. Source of Truth

MQTT messages are the primary source of system state.

The Leitstelle maintains an internal state derived from received MQTT messages.

The REST endpoints:

```text
GET /map-data
GET /status
```

must use this MQTT-derived state as their primary data source.

---

# 13. Planned Failure Scenarios

The following scenarios will be tested:

1. Sensor container failure
2. Sensor container restart
3. Broker restart
4. Duplicate incident publication
5. Old message publication

Additional failure scenarios may be added later.
