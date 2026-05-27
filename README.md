# Distributed Flood Response System — Sturmflut Nordsee

---

# Overview

This repository contains the implementation of a distributed disaster-response system .

The project simulates emergency coordination on a fictional North Sea island after a severe storm flood. Multiple distributed components communicate over different protocols to monitor the environment, report incidents, coordinate autonomous vehicles, and visualize the current system state through a browser-based dashboard.

The system is implemented using communication methods such as raw TCP sockets and manually parsed HTTP requests .
---

# Project Goals

The project focuses on:

- distributed system architecture
- inter-process communication
- custom HTTP communication
- REST-based service interaction
- RPC communication
- event-driven incident management
- infrastructure monitoring
- containerized deployment
- automated testing
- reproducibility and observability


---

# Scenario

After a storm flood, the island infrastructure becomes partially damaged and inaccessible.

A central control center coordinates:

- autonomous vehicles
- environmental sensors
- incidents
- infrastructure monitoring
- islandmap visualization

Sensors continuously monitor the island and generate alerts when dangerous situations occur. Vehicles are intended to react to incidents and operate across different terrain types.

The entire system is deployed as distributed system running in separate containers.

---

# Implemented Milestone

## Aufgabe 1 — Leitstelle und Registrierung via Sockets, HTTP und REST

The current implementation includes:

- custom TCP-based HTTP server
- manual HTTP parsing
- REST API implementation without frameworks
- registration of vehicles and sensors
- incident creation and management
- dashboard visualization
- island map representation
- functional tests
- non-functional tests
- latency and concurrency measurements
- Docker-based deployment


---

# System Architecture

> Architecture diagram placeholder  
> *(Diagram will be added soon.)*


---

# Core Components

## Control Center

The control center is the central component of the system and acts as the main coordination and communication service.

Responsibilities include:

- accepting TCP connections
- parsing HTTP requests
- request routing
- REST endpoint handling
- registration of vehicles and sensors
- incident management
- dashboard rendering
- island map management
- system status 

The HTTP server is implemented manually without using Flask, FastAPI, Django, or other HTTP frameworks.

### Important Modules

| Module | Purpose |
|---|---|
| `tcpserversocket.py` | TCP socket server |
| `parsing.py` | Manual HTTP request parsing |
| `routes.py` | Route management |
| `handlers.py` | Endpoint request handling |
| `state.py` | Shared system state |
| `status.py` | Global status generation |

---

## Dashboard

The dashboard provides a browser-accessible visualization of the current system state with Islandmap and status tabel.

### Endpoint

```text
GET /dashboard
```

The dashboard is generated dynamically by the custom HTTP server and rendered directly inside a web browser.

### Dashboard Features

The dashboard visualizes:

- registered vehicles
- active sensors
- incidents sent by sensors
- map visualization
- infrastructure elements
- system statistics
- unit positions
- incident details

The dashboard demonstrates browser-compatible HTTP rendering without external web frameworks.

---

## Vehicles

The system currently supports three autonomous vehicle types.

| Vehicle | Description |
|---|---|
| Drone | Ground-based and Water-based unit |
| Rover | Ground-based exploration unit |
| Boat | Water-based transport unit |

Vehicles register themselves through the REST API and are managed by the control center and assighned missions.

Missions are assigned to the vehicles through a RPC-based coordination.

---

## Sensors

Different sensor types monitor the environment and automatically generate incidents when thresholds are exceeded.

### Implemented Sensor Types

| Sensor | Purpose |
|---|---|
| Camera Sensor | Person detection |
| Water Sensor | Water level monitoring |
| Vibration Sensor | High vibration monitoring |

Sensors simulate environmental measurements and continuously interact with the control center by reporting incidents.

---

# Incident Management

The system supports centralized incident processing and monitoring.

## Supported Incident Types

| Incident Type | Description |
|---|---|
| `person_detected` | Person detected by camera |
| `water_level_alert` | Water level exceeded threshold |
| `vibration_detected` | Dangerous structural vibration detected |

Each incident contains:

- unique incident ID
- source sensor ID
- message
- priority
- position
- incident type

Incidents are stored in the global system state and displayed in the dashboard.

---

# Island Map

The project contains a dynamically managed island map.

## Map Properties

| Property | Value |
|---|---|
| Grid Size | 20 × 20 |
| Terrain Types | Land / Water |

Each map cell represents either:

- land
- water

---

# Infrastructure

The map includes predefined solid infrastructure .

## Implemented Infrastructure

| Infrastructure | Count |
|---|---|
| Harbors | 2 |
| Charging Stations | 2 |
| Depot | 1 |
| Landing Field | 1 |
| Bridges | Multiple |

Infrastructure information is integrated into the map and dashboard visualization through different colors.

---

# Communication Technologies

The project intentionally combines multiple communication technologies commonly used in distributed systems.

| Technology | Usage |
|---|---|
| TCP Sockets | Low-level HTTP communication |
| HTTP | Browser communication |
| REST API | Registration and incident handling |
| RPC | Vehicle coordination foundation |
| Docker Networking | Inter-container communication |
| Protocol Buffers | RPC interface definition |

---

# REST API

The REST interface is implemented manually using raw TCP sockets and custom request parsing.

## Supported Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/unit` | Register vehicle or sensor |
| POST | `/incident` | Create incident |
| GET | `/status` | Retrieve global system state ,currently JSON |
| GET | `/map` | Retrieve island map |
| GET | `/dashboard` | Open monitoring dashboard |

---

# Example API Requests

## Register Vehicle

```http
POST /unit
Content-Type: application/json

{
  "id": "drone-1",
  "unit": "vehicle",
  "vehicle_type": "drone",
  "position": {
    "x": 5,
    "y": 12
  }
}
```

---

## Register Sensor

```http
POST /unit
Content-Type: application/json

{
  "id": "camera-1",
  "unit": "sensor",
  "sensor_type": "camera",
  "position": {
    "x": 10,
    "y": 12
  }
}
```

---

## Create Incident

```http
POST /incident
Content-Type: application/json

{
  "id": "incident-1",
  "incident_type": "person_detected",
  "source_id": "camera-1",
  "message": "Person Detected with High-Probability",
  "position": {
    "x": 10,
    "y": 12
  },
  "priority": 2,
  "status": "open"
}
```

---

# RPC Layer

Control center assigns missions to vehicles through RPC commnunication

## RPC Components

| File | Purpose |
|---|---|
| `dispatcher.py` | Mission request distribution |
| `mission_pb2_grpc.py` | Generated protobuf messages |
| `mission_pb2.py` | Generated gRPC service bindings |
| `rpc_server.py` | RPC server implementation |
| `mission.proto` | Protocol Buffers definition |

The RPC layer is intended for:

- mission assignment
- vehicle communication


---

# Project Structure

```text
DoY5BlockTeamF/
│
├── app/
│   ├── control_center/
│   ├── dashboard/
│   ├── sensors/
│   ├── vehicles/
│   ├── common/
│   └── rpc/
│
├── tests/
├── docs/
├── proto/
├── assets/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

# Technologies

| Technology | Purpose |
|---|---|
| Python | Main implementation |
| Docker | Containerization |
| Docker Compose | Multi-container orchestration |
| TCP Sockets | networking |
| pytest | Automated testing |
| requests | REST API testing |
| threading | Concurrency testing |
| Protocol Buffers | RPC interface definitions |

---

# Running the System

## Requirements

- Docker
- Docker Compose
- Python 3.14+

---

# Start the System

```bash
docker compose up 
```

---

# Access the Dashboard

Open in browser:

```text
http://localhost:8080/dashboard
```

---

# Testing

The repository contains functional and non-functional tests.

---

# Deploy containers

```bash
docker compose up
```

---

# Run All Tests

```bash
pytest -v
```

---

# Implemented Tests

## Functional Tests

- vehicle registration
- sensor registration
- incident creation
- duplicate prevention
- invalid request handling
- unsupported method handling
- unknown route validation
- dashboard endpoint validation

---

## Non-Functional Tests

- latency measurement
- average response-time testing
- concurrent request handling
- burst request testing
- stability measurements

---

# Example Test Result

```text
==============================
19 passed in 0.33s
==============================
```

---

# Design Decisions

## Manual HTTP Implementation

The project intentionally avoids external web frameworks in order to better understand:

- TCP communication
- HTTP protocol structure
- socket handling
- request parsing
- routing
- response generation
- distributed communication

---

## Distributed Architecture

The system is designed as a distributed multi-component architecture where:

- sensors
- vehicles
- dashboard
- RPC services
- control center

operate as independent logical components.

---

## Containerization

The project uses Docker and Docker Compose to ensure:

- reproducible deployments
- isolated execution environments
- simplified distributed setup

---

# Future Milestones

Planned future extensions include:

- RPC-based mission assignment
- MQTT-based event communication
- ...

---
