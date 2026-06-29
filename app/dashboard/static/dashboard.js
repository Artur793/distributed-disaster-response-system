let mapData = null;
let lastStatus = null;
let missionFilter = "active";

const markerLabels = {
    drone: "D",
    rover: "R",
    boat: "B",
    camera: "C",
    water: "W",
    vibration: "V",
};

function positionText(position) {
    return position ? `(${position.x}, ${position.y})` : "N/A";
}

function setText(id, value) {
    document.getElementById(id).textContent = value;
}

function makeCell(text) {
    const cell = document.createElement("td");
    cell.textContent = text;
    return cell;
}

function renderEmpty(tbody, colspan) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.className = "empty";
    cell.colSpan = colspan;
    cell.textContent = "No entries";
    row.appendChild(cell);
    tbody.appendChild(row);
}

function appendProgressCell(row, progress) {
    const cell = document.createElement("td");
    const display = document.createElement("div");
    const track = document.createElement("div");
    const fill = document.createElement("div");
    const value = document.createElement("span");
    const boundedProgress = Math.min(100, Math.max(0, progress || 0));

    display.className = "progress";
    track.className = "progress-track";
    fill.className = "progress-fill";
    fill.style.width = `${boundedProgress}%`;
    value.textContent = `${boundedProgress}%`;
    track.appendChild(fill);
    display.append(track, value);
    cell.appendChild(display);
    row.appendChild(cell);
}

function renderVehicles(vehicles) {
    const tbody = document.getElementById("vehicles-body");
    tbody.replaceChildren();

    if (!vehicles.length) {
        renderEmpty(tbody, 6);
        return;
    }

    vehicles.forEach((vehicle) => {
        const row = document.createElement("tr");
        row.appendChild(makeCell(vehicle.id));
        row.appendChild(makeCell(vehicle.vehicle_type));
        row.appendChild(makeCell(positionText(vehicle.position)));
        row.appendChild(makeCell(vehicle.status));
        row.appendChild(makeCell(vehicle.assigned_mission_id || "N/A"));
        appendProgressCell(row, vehicle.progress);
        tbody.appendChild(row);
    });
}

function renderSensors(sensors) {
    const tbody = document.getElementById("sensors-body");
    tbody.replaceChildren();

    if (!sensors.length) {
        renderEmpty(tbody, 4);
        return;
    }

    sensors.forEach((sensor) => {
        const row = document.createElement("tr");
        row.appendChild(makeCell(sensor.id));
        row.appendChild(makeCell(sensor.sensor_type));
        row.appendChild(makeCell(positionText(sensor.position)));
        row.appendChild(makeCell(sensor.status));
        tbody.appendChild(row);
    });
}

function renderIncidents(incidents) {
    const tbody = document.getElementById("incidents-body");
    tbody.replaceChildren();

    if (!incidents.length) {
        renderEmpty(tbody, 5);
        return;
    }

    incidents.forEach((incident) => {
        const row = document.createElement("tr");
        row.appendChild(makeCell(incident.id));
        row.appendChild(makeCell(incident.incident_type));
        row.appendChild(makeCell(positionText(incident.position)));
        row.appendChild(makeCell(String(incident.priority)));
        row.appendChild(makeCell(incident.status));
        tbody.appendChild(row);
    });
}

function filteredMissions(missions) {
    if (missionFilter === "completed") {
        return missions.filter((mission) => mission.status === "COMPLETED");
    }
    if (missionFilter === "active") {
        return missions.filter((mission) => mission.status !== "COMPLETED");
    }
    return missions;
}

function renderMissions(missions) {
    const tbody = document.getElementById("missions-body");
    tbody.replaceChildren();
    const filtered = filteredMissions(missions);

    if (!filtered.length) {
        renderEmpty(tbody, 6);
        return;
    }

    filtered.forEach((mission) => {
        const row = document.createElement("tr");
        row.appendChild(makeCell(mission.id));
        row.appendChild(makeCell(mission.assigned_vehicle_id || "N/A"));
        row.appendChild(makeCell(mission.area_type));
        row.appendChild(makeCell(mission.status));
        appendProgressCell(row, mission.progress);
        row.appendChild(makeCell(mission.result_message || "N/A"));
        tbody.appendChild(row);
    });
}

function renderMapBase() {
    if (!mapData) {
        return;
    }

    const grid = document.getElementById("map-grid");
    const yAxis = document.getElementById("map-y-axis");
    const xAxis = document.getElementById("map-x-axis");
    grid.style.setProperty("--map-width", mapData.width);
    yAxis.style.setProperty("--map-height", mapData.height);
    xAxis.style.setProperty("--map-width", mapData.width);
    grid.replaceChildren();
    yAxis.replaceChildren();
    xAxis.replaceChildren();

    for (let y = 0; y < mapData.height; y += 1) {
        const label = document.createElement("span");
        label.textContent = String(y);
        yAxis.appendChild(label);
    }

    for (let x = 0; x < mapData.width; x += 1) {
        const label = document.createElement("span");
        label.textContent = String(x);
        xAxis.appendChild(label);
    }

    mapData.cells.flat().forEach((cell) => {
        const tile = document.createElement("div");
        const markerLayer = document.createElement("div");
        tile.className = `map-cell ${cell.tile_type}`;
        if (cell.infrastructure) {
            tile.classList.add(cell.infrastructure);
            tile.title = cell.infrastructure.replaceAll("_", " ");
        }
        tile.dataset.x = cell.x;
        tile.dataset.y = cell.y;
        markerLayer.className = "marker-layer";
        tile.appendChild(markerLayer);
        grid.appendChild(tile);
    });
}

function markerFor(type, item, label) {
    const marker = document.createElement("span");
    marker.className = `marker ${type}`;
    marker.textContent = label;
    marker.title = `${type}: ${item.id}`;
    return marker;
}

function markerForGroup(type, items, singleLabel) {
    const label = items.length > 1 ? String(items.length) : singleLabel(items[0]);
    const marker = markerFor(type, items[0], label);
    if (items.length > 1) {
        marker.classList.add("multiple");
        marker.title = `${type}s: ${items.map((item) => item.id).join(", ")}`;
    }
    return marker;
}

function placeMarker(position, marker) {
    if (!position) {
        return;
    }
    const layer = document.querySelector(
        `.map-cell[data-x="${position.x}"][data-y="${position.y}"] .marker-layer`
    );
    if (layer) {
        layer.appendChild(marker);
    }
}

function groupByPosition(items) {
    const groups = new Map();

    items.filter((item) => item.position).forEach((item) => {
        const key = `${item.position.x},${item.position.y}`;
        if (!groups.has(key)) {
            groups.set(key, []);
        }
        groups.get(key).push(item);
    });

    return groups.values();
}

function renderMarkers(status) {
    document.querySelectorAll(".marker-layer").forEach((layer) => {
        layer.replaceChildren();
    });

    groupByPosition(status.vehicles).forEach((vehicles) => {
        placeMarker(
            vehicles[0].position,
            markerForGroup(
                "vehicle",
                vehicles,
                (vehicle) => markerLabels[vehicle.vehicle_type] || "U"
            )
        );
    });
    groupByPosition(status.sensors).forEach((sensors) => {
        placeMarker(
            sensors[0].position,
            markerForGroup(
                "sensor",
                sensors,
                (sensor) => markerLabels[sensor.sensor_type] || "S"
            )
        );
    });
    groupByPosition(status.incidents).forEach((incidents) => {
        placeMarker(
            incidents[0].position,
            markerForGroup("incident", incidents, () => "!")
        );
    });
}

function renderCharging(charging) {

    if (!charging) {
        return;
    }

    setText(
        "charging-resource",
        charging.resource_id || "-"
    );

    setText(
        "charging-holder",
        charging.current_holder || "-"
    );

    setText(
        "charging-waiting",
        charging.waiting_vehicles.length
            ? charging.waiting_vehicles.join(", ")
            : "-"
    );

    const safety =
    document.getElementById(
        "charging-safety"
    );

    safety.textContent =
        charging.safety_violation
            ? "SAFETY VIOLATION"
            : "OK";

    safety.className =
        charging.safety_violation
            ? "safety-warning"
            : "safety-ok";

    const tbody =
        document.getElementById(
            "charging-body"
        );

    tbody.replaceChildren();

    if (
        !charging.participants ||
        charging.participants.length === 0
    ) {

        renderEmpty(tbody, 7);

        return;
    }

    charging.participants.forEach(
        (participant) => {

            const row =
                document.createElement("tr");

            row.appendChild(
                makeCell(participant.vehicle_id)
            );

            row.appendChild(
                makeCell(participant.vehicle_state)
            );

            row.appendChild(
                makeCell(participant.ra_state)
            );

            row.appendChild(
                makeCell(
                    String(participant.lamport)
                )
            );

            row.appendChild(
                makeCell(
                    `${participant.battery_percent}%`
                )
            );

            row.appendChild(
                makeCell(

                    participant.waiting_for.length

                        ? participant.waiting_for.join(", ")

                        : "-"

                )
            );

            row.appendChild(
                makeCell(

                    participant.deferred_replies.length

                        ? participant.deferred_replies.join(", ")

                        : "-"

                )
            );

            tbody.appendChild(row);

        }
    );

}

function renderStatus(status) {
    setText("vehicle-count", status.vehicle_count);
    setText("sensor-count", status.sensor_count);
    setText("incident-count", status.incident_count);
    setText("mission-count", status.mission_count);
    renderVehicles(status.vehicles);
    renderSensors(status.sensors);
    renderIncidents(status.incidents);
    renderMissions(status.missions);
    renderMarkers(status);
    renderCharging(
        status.charging_coordination
    );
}

async function loadMap() {
    try {
        const response = await fetch("/map-data");
        if (!response.ok) {
            return;
        }
        mapData = await response.json();
        renderMapBase();
        if (lastStatus) {
            renderMarkers(lastStatus);
        }
    } catch (error) {
        return;
    }
}

async function refreshStatus() {
    try {
        const response = await fetch("/status");
        if (!response.ok) {
            return;
        }
        lastStatus = await response.json();
        renderStatus(lastStatus);
    } catch (error) {
        return;
    }
}

document.querySelectorAll(".filter button").forEach((button) => {
    button.addEventListener("click", () => {
        missionFilter = button.dataset.filter;
        document.querySelectorAll(".filter button").forEach((candidate) => {
            candidate.classList.toggle("selected", candidate === button);
        });
        if (lastStatus) {
            renderMissions(lastStatus.missions);
        }
    });
});

loadMap();
refreshStatus();
window.setInterval(refreshStatus, 250);
