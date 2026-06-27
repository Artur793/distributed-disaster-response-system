import json
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from app.common.models import (
    Incident,
    IncidentType,
    Mission,
    Position,
)
from app.common.state import SystemState


class MQTTSubscriber:
    BROKER_HOST = "mosquitto"
    BROKER_PORT = 1883
    STARTUP_RETRY_SECONDS = 5
    MAX_MESSAGE_AGE_SECONDS = 60
    INCIDENT_DUPLICATE_WINDOW_SECONDS = 30

    def __init__(self, state: SystemState):
        self.state = state

        self.processed_message_ids = set()

        self.recent_incidents = {}

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="leitstelle",
        )

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        self.client.reconnect_delay_set(
            min_delay=5,
            max_delay=30,
        )

    def start(self):
        while True:
            try:
                self.client.connect(
                    self.BROKER_HOST,
                    self.BROKER_PORT,
                    60,
                )
                break
            except OSError as error:
                print(
                    "MQTT broker unavailable "
                    f"({error}); retrying in "
                    f"{self.STARTUP_RETRY_SECONDS}s"
                )
                time.sleep(self.STARTUP_RETRY_SECONDS)

        self.client.loop_start()

        print("MQTT subscriber started")

    def on_connect(
        self,
        client,
        userdata,
        flags,
        reason_code,
        properties,
    ):
        print("Connected to MQTT broker")

        client.subscribe("island/events/#", qos=1)
        client.subscribe("island/telemetry/#", qos=0)
        client.subscribe("island/status/#", qos=1)
        client.subscribe("island/coordination/charging/status",qos=1,)

    def on_disconnect(
        self,
        client,
        userdata,
        disconnect_flags,
        reason_code,
        properties,
    ):
        print(f"MQTT disconnected: {reason_code}")

    def on_message(
        self,
        client,
        userdata,
        msg,
    ):
        try:
            payload = json.loads(msg.payload.decode())
        except Exception:
            print("Invalid MQTT JSON")
            return

        if not self._validate_message(payload, msg.topic):
            return

        topic = msg.topic

        if topic.startswith("island/events"):
            self._handle_incident(payload)

        elif topic.startswith("island/telemetry"):
            self._handle_telemetry(payload)

        elif topic.startswith("island/status"):
            self._handle_status(payload)
        
        elif topic.startswith("island/coordination/charging/status"):
            self._handle_charging_status(payload)

    def _validate_message(self, payload: dict, topic: str) -> bool:
        message_id = payload.get("message_id")

        if not message_id:
            return False

        if message_id in self.processed_message_ids:
            print(f"Duplicate message ignored: {message_id}")
            return False

        timestamp_string = payload.get("timestamp")
        should_check_message_age = not topic.startswith("island/status")

        if should_check_message_age and not timestamp_string:
            return False

        if timestamp_string and should_check_message_age:
            try:
                timestamp = datetime.fromisoformat(
                    timestamp_string.replace("Z", "+00:00")
                )

                age = (
                    datetime.now(timezone.utc) - timestamp
                ).total_seconds()

                if age > self.MAX_MESSAGE_AGE_SECONDS:
                    print(
                        f"Old message rejected ({age:.1f}s): {message_id}"
                    )
                    return False

            except Exception:
                return False

        self.processed_message_ids.add(message_id)

        return True

    def _handle_incident(self, payload: dict):
        try:
            position = payload["position"]

            duplicate_key = (
                payload["incident_type"],
                position["x"],
                position["y"],
            )

            now = time.time()

            if duplicate_key in self.recent_incidents:
                age = now - self.recent_incidents[duplicate_key]

                if age < self.INCIDENT_DUPLICATE_WINDOW_SECONDS:
                    print(
                        f"Incident duplicate ignored: {duplicate_key}"
                    )
                    return

            self.recent_incidents[duplicate_key] = now

            island_map = self.state.get_map()

            area_type = (
                island_map
                .cells[position["y"]][position["x"]]
                .tile_type
                .name
            )

            incident = Incident(
                id=payload["id"],
                incident_type=IncidentType(
                    payload["incident_type"]
                ),
                source_id=payload["source_id"],
                message=payload["message"],
                position=Position(
                    x=position["x"],
                    y=position["y"],
                ),
                priority=payload.get("priority", 1),
                status=payload.get("status", "open"),
            )

            if not self.state.add_incident(incident):
                return

            mission = Mission(
                id=incident.id,
                incident_id=incident.id,
                incident_type=incident.incident_type,
                target_position=incident.position,
                priority=incident.priority,
                area_type=area_type,
            )

            self.state.add_mission(mission)

            print(
                f"MQTT incident received: {incident.id}"
            )

        except Exception as e:
            print(f"Incident processing failed: {e}")

    def _handle_telemetry(self, payload: dict):
        try:
            vehicle_id = payload["vehicle_id"]

            vehicle = self.state.get_vehicle(vehicle_id)

            if vehicle is None:
                return

            position = payload.get("position")

            self.state.update_vehicle_status(
                vehicle_id,
                payload.get("state", vehicle.status),
                payload.get("progress_percent", 0),
                payload.get("result"),
                Position(
                    x=position["x"],
                    y=position["y"],
                ) if position else None,
            )

        except Exception as e:
            print(f"Telemetry processing failed: {e}")

    def _handle_status(self, payload: dict):
        try:
            vehicle_id = payload["vehicle_id"]

            vehicle = self.state.get_vehicle(vehicle_id)

            if vehicle is None:
                return

            self.state.update_vehicle_status(
                vehicle_id,
                payload["status"],
                vehicle.progress,
                payload.get("result"),
                vehicle.position,
            )

        except Exception as e:
            print(f"Status processing failed: {e}")
    
    def _handle_charging_status(
    self,
    payload: dict,):

        try:

            required_fields = [

                "vehicle_id",

                "vehicle_state",

                "ra_state",

                "lamport",

                "battery_percent",

            ]

            for field in required_fields:

                if field not in payload:

                    print(
                        f"Charging status missing field: {field}"
                    )

                    return

            self.state.update_charging_status(payload)

            charging = self.state.get_charging_status()

            print(
                f"[Charging] "
                f"{payload['vehicle_id']} "
                f"{payload['ra_state']} "
                f"(Lamport {payload['lamport']})"
            )

            if charging["safety_violation"]:

                print()

                print(
                    "===================================="
                )

                print(
                    "SAFETY VIOLATION DETECTED"
                )

                print(
                    "Multiple vehicles entered HELD."
                )

                print(
                    f"Current holder(s): "
                    f"{charging['current_holder']}"
                )

                print(
                    "===================================="
                )

                print()

        except Exception as error:

            print(

                f"Charging status processing failed: "

                f"{error}"

            )
