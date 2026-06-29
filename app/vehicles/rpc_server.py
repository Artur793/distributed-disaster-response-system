import json
import threading
import time
from concurrent import futures

import grpc

from app.rpc.generated import mission_pb2
from app.rpc.generated import mission_pb2_grpc
from app.common.mqtt_publisher import (
    MessageIdGenerator,
    connect_mqtt_client,
    message_envelope,
    publish_json,
    utc_timestamp,
)
from app.vehicles.charging_coordinator import (
    RequestDecision,
    VehicleChargingCoordinator,
)


class BaseVehicle(mission_pb2_grpc.VehicleServiceServicer):

    def __init__(self, vehicle_id: str, vehicle_type: str):
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type

        self.state = mission_pb2.IDLE
        self.progress = 0
        self.result_message = ""

        self.current_mission = None
        self.message_ids = MessageIdGenerator()
        self.telemetry_topic = f"island/telemetry/{self.vehicle_id}"
        self.status_topic = f"island/status/{self.vehicle_id}"
        self.charging_request_topic = "island/coordination/charging/request"
        self.charging_reply_topic = (
            f"island/coordination/charging/reply/{self.vehicle_id}"
        )
        self.charging_status_topic = "island/coordination/charging/status"
        self.mqtt_client = None
        self._charging_status_thread_started = False
        self._charging_thread_started = False
        self.charging_coordinator = (
            VehicleChargingCoordinator.from_environment(self.vehicle_id)
        )

    
    def AssignMission(self, request, context): # implement the assignmission of rpc

        print(
            f"[{self.vehicle_id}] mission received: "
            f"{request.mission_id}"
        )

        if self.state != mission_pb2.IDLE:
            return mission_pb2.MissionAck(
                mission_id=request.mission_id,
                vehicle_id=self.vehicle_id,
                accepted=False,
                message="Vehicle is not idle",
            )

        if not self.is_compatible(request):
            print("not compatible")

            return mission_pb2.MissionAck(
                mission_id=request.mission_id,
                vehicle_id=self.vehicle_id,
                accepted=False,
                message="Mission incompatible with vehicle role",
            )
            
        print("compatible")
        self.current_mission = request
        self.state = mission_pb2.ASSIGNED
        self.progress = 0
        self.result_message = ""
        self.publish_telemetry()

        thread = threading.Thread(
            target=self.execute_mission,
            daemon=True,
        )
        thread.start()

        return mission_pb2.MissionAck(
            mission_id=request.mission_id,
            vehicle_id=self.vehicle_id,
            accepted=True,
            message="Mission accepted",
        )

   
    def GetVehicleStatus(self, request, context): # implement the get vehicle status of rpc

        return mission_pb2.VehicleStatus(
            vehicle_id=self.vehicle_id,
            state=self.state,
            assigned_mission_id=(
                self.current_mission.mission_id
                if self.current_mission
                else ""
            ),
            progress_percent=self.progress,
            result=self.result_message,
            current_position=mission_pb2.Position(
                x=self.position["x"],
                y=self.position["y"],
            ),
        )

    def start_mqtt_telemetry(self) -> None:
        will_payload = {
            **message_envelope(self.vehicle_id, self.message_ids),
            "vehicle_id": self.vehicle_id,
            "status": "ERROR",
            "result": "Unexpected MQTT disconnect",
        }
        self.mqtt_client = connect_mqtt_client(
            client_id=self.vehicle_id,
            will_topic=self.status_topic,
            will_payload=will_payload,
            will_qos=1,
        )
        self.configure_charging_mqtt()
        self.publish_telemetry()
        self.start_charging_status_publisher()
        self.publish_charging_status()

    def configure_charging_mqtt(self) -> None:
        if (
            self.mqtt_client is None
            or not self.charging_coordinator.enabled
        ):
            return

        self.mqtt_client.on_connect = self._on_charging_mqtt_connect
        self.mqtt_client.on_message = self._on_charging_mqtt_message
        self.subscribe_charging_topics()

    def _on_charging_mqtt_connect(
        self,
        client,
        userdata,
        flags,
        reason_code,
        properties,
    ) -> None:
        self.subscribe_charging_topics()

    def subscribe_charging_topics(self) -> None:
        if self.mqtt_client is None:
            return

        self.mqtt_client.subscribe(self.charging_request_topic, qos=1)
        self.mqtt_client.subscribe(self.charging_reply_topic, qos=1)
        print(
            f"[{self.vehicle_id}] subscribed to RA charging topics"
        )

    def _on_charging_mqtt_message(
        self,
        client,
        userdata,
        msg,
    ) -> None:
        try:
            payload = json.loads(msg.payload.decode())
        except Exception:
            print(f"[{self.vehicle_id}] invalid charging MQTT JSON")
            return

        if msg.topic == self.charging_request_topic:
            self.handle_charging_request(payload)
        elif msg.topic == self.charging_reply_topic:
            self.handle_charging_reply(payload)

    def publish_telemetry(self) -> None:
        if self.mqtt_client is None:
            return

        payload = {
            **message_envelope(self.vehicle_id, self.message_ids),
            "vehicle_id": self.vehicle_id,
            "position": {
                "x": self.position["x"],
                "y": self.position["y"],
            },
            "state": mission_pb2.VehicleState.Name(self.state),
            "assigned_mission_id": (
                self.current_mission.mission_id
                if self.current_mission
                else None
            ),
            "progress_percent": self.progress,
            "result": self.result_message or None,
        }
        publish_json(
            self.mqtt_client,
            self.telemetry_topic,
            payload,
            qos=0,
        )
        self.maybe_request_charging()

    def maybe_request_charging(self) -> None:
        if self.state != mission_pb2.IDLE:
            return

        if self.charging_coordinator.needs_charging():
            self.request_charging_access()

    def start_charging_status_publisher(self) -> None:
        if (
            self._charging_status_thread_started
            or not self.charging_coordinator.enabled
        ):
            return

        self._charging_status_thread_started = True
        thread = threading.Thread(
            target=self._charging_status_loop,
            daemon=True,
        )
        thread.start()

    def _charging_status_loop(self) -> None:
        while True:
            time.sleep(1)
            snapshot = self.charging_coordinator.snapshot()
            if self.charging_coordinator.should_log_timeout_warning(
                time.time()
            ):
                print(
                    f"[{self.vehicle_id}] still waiting for RA REPLYs: "
                    f"{snapshot.waiting_for}"
                )
            if snapshot.needs_periodic_status:
                self.publish_charging_status(snapshot)
            if snapshot.ra_state == "WANTED":
                self.republish_charging_request()

    def publish_charging_status(self, snapshot=None) -> None:
        if (
            self.mqtt_client is None
            or not self.charging_coordinator.enabled
        ):
            return

        snapshot = snapshot or self.charging_coordinator.snapshot()
        payload = {
            "message_id": self.message_ids.next(self.vehicle_id),
            "type": "STATUS",
            "resource_id": snapshot.resource_id,
            "sender_id": self.vehicle_id,
            "vehicle_id": self.vehicle_id,
            "vehicle_state": mission_pb2.VehicleState.Name(self.state),
            "ra_state": snapshot.ra_state,
            "lamport": snapshot.lamport,
            "waiting_for": snapshot.waiting_for,
            "deferred_replies": snapshot.deferred_replies,
            "battery_percent": snapshot.battery_percent,
            "sent_at": utc_timestamp(),
        }
        publish_json(
            self.mqtt_client,
            self.charging_status_topic,
            payload,
            qos=1,
        )

    def request_charging_access(self) -> None:
        if self.mqtt_client is None:
            return

        request = self.charging_coordinator.start_request()
        if request is None:
            return

        payload = {
            "message_id": self.message_ids.next(self.vehicle_id),
            "type": "REQUEST",
            "resource_id": self.charging_coordinator.config.resource_id,
            "sender_id": self.vehicle_id,
            "lamport": request.lamport,
            "request_id": request.request_id,
            "battery_percent": request.battery_percent,
            "reason": "LOW_BATTERY",
            "sent_at": utc_timestamp(),
        }
        publish_json(
            self.mqtt_client,
            self.charging_request_topic,
            payload,
            qos=1,
        )
        print(
            f"[{self.vehicle_id}] sent RA REQUEST "
            f"{request.request_id}"
        )
        self.publish_charging_status()
        self.start_charging_if_held()

    def republish_charging_request(self) -> None:
        if self.mqtt_client is None:
            return

        request = self.charging_coordinator.current_request()
        if request is None:
            return

        payload = {
            "message_id": self.message_ids.next(self.vehicle_id),
            "type": "REQUEST",
            "resource_id": self.charging_coordinator.config.resource_id,
            "sender_id": self.vehicle_id,
            "lamport": request.lamport,
            "request_id": request.request_id,
            "battery_percent": request.battery_percent,
            "reason": "LOW_BATTERY",
            "sent_at": utc_timestamp(),
        }
        publish_json(
            self.mqtt_client,
            self.charging_request_topic,
            payload,
            qos=1,
        )
        print(
            f"[{self.vehicle_id}] republished RA REQUEST "
            f"{request.request_id}"
        )

    def handle_charging_request(self, payload: dict) -> None:
        required_fields = {
            "message_id",
            "resource_id",
            "sender_id",
            "lamport",
            "request_id",
        }
        if not required_fields.issubset(payload):
            print(f"[{self.vehicle_id}] charging REQUEST missing fields")
            return

        if (
            payload["resource_id"]
            != self.charging_coordinator.config.resource_id
        ):
            return

        decision = self.charging_coordinator.receive_request(
            message_id=payload["message_id"],
            request_id=payload["request_id"],
            sender_id=payload["sender_id"],
            lamport=payload["lamport"],
        )

        if decision == RequestDecision.REPLY:
            self.send_charging_reply(
                target_vehicle_id=payload["sender_id"],
                request_id=payload["request_id"],
            )
        elif decision == RequestDecision.DEFER:
            print(
                f"[{self.vehicle_id}] deferred RA REPLY to "
                f"{payload['sender_id']}"
            )

        if decision != RequestDecision.IGNORE:
            self.publish_charging_status()

    def send_charging_reply(
        self,
        *,
        target_vehicle_id: str,
        request_id: str,
    ) -> None:
        if self.mqtt_client is None:
            return

        lamport = self.charging_coordinator.next_lamport()
        payload = {
            "message_id": self.message_ids.next(self.vehicle_id),
            "type": "REPLY",
            "resource_id": self.charging_coordinator.config.resource_id,
            "sender_id": self.vehicle_id,
            "target_vehicle_id": target_vehicle_id,
            "lamport": lamport,
            "request_id": request_id,
            "sent_at": utc_timestamp(),
        }
        publish_json(
            self.mqtt_client,
            f"island/coordination/charging/reply/{target_vehicle_id}",
            payload,
            qos=1,
        )
        print(
            f"[{self.vehicle_id}] sent RA REPLY to "
            f"{target_vehicle_id} for {request_id}"
        )

    def handle_charging_reply(self, payload: dict) -> None:
        required_fields = {
            "message_id",
            "resource_id",
            "sender_id",
            "target_vehicle_id",
            "lamport",
            "request_id",
        }
        if not required_fields.issubset(payload):
            print(f"[{self.vehicle_id}] charging REPLY missing fields")
            return

        if (
            payload["resource_id"]
            != self.charging_coordinator.config.resource_id
        ):
            return

        entered_held = self.charging_coordinator.receive_reply(
            message_id=payload["message_id"],
            request_id=payload["request_id"],
            sender_id=payload["sender_id"],
            target_vehicle_id=payload["target_vehicle_id"],
            lamport=payload["lamport"],
        )

        if entered_held:
            print(
                f"[{self.vehicle_id}] entered RA HELD for charging"
            )
            self.start_charging_if_held()

        self.publish_charging_status()

    def start_charging_if_held(self) -> None:
        if (
            self._charging_thread_started
            or not self.charging_coordinator.is_held()
        ):
            return

        self._charging_thread_started = True
        thread = threading.Thread(
            target=self._charging_loop,
            daemon=True,
        )
        thread.start()

    def _charging_loop(self) -> None:
        print(f"[{self.vehicle_id}] travelling to charging station")
        self.state = mission_pb2.BUSY
        self.progress = 0
        self.result_message = "Travelling to charging station"
        self.publish_telemetry()
        self.publish_charging_status()

        try:
            self.travel_to_charging_station()

            print(f"[{self.vehicle_id}] starting charging simulation")
            self.state = mission_pb2.CHARGING
            self.result_message = "Charging"
            self.publish_telemetry()
            self.publish_charging_status()

            while not self.charging_coordinator.is_fully_charged():
                time.sleep(1)
                battery_percent = (
                    self.charging_coordinator.charge_one_tick()
                )
                print(
                    f"[{self.vehicle_id}] charging battery "
                    f"{battery_percent}%"
                )
                self.publish_charging_status()

            deferred_replies = (
                self.charging_coordinator.finish_charging()
            )
            self.state = mission_pb2.IDLE
            self.progress = 0
            self.result_message = ""
            self.publish_telemetry()

            for target_vehicle_id, request_id in deferred_replies:
                self.send_charging_reply(
                    target_vehicle_id=target_vehicle_id,
                    request_id=request_id,
                )

            print(f"[{self.vehicle_id}] finished charging")
            self.publish_charging_status()

        finally:
            self._charging_thread_started = False

    def travel_to_charging_station(self) -> None:
        target = (
            self.charging_coordinator
            .config
            .charging_station_position
        )

        while self.position != target:
            time.sleep(1)
            if self.position["x"] < target["x"]:
                self.position["x"] += 1
            elif self.position["x"] > target["x"]:
                self.position["x"] -= 1
            elif self.position["y"] < target["y"]:
                self.position["y"] += 1
            elif self.position["y"] > target["y"]:
                self.position["y"] -= 1

            print(
                f"[{self.vehicle_id}] moving to charging station "
                f"({self.position['x']}, {self.position['y']})"
            )
            self.publish_telemetry()

    def travel_to_mission(self) -> None:
        self.state = mission_pb2.BUSY
        self.progress = 0
        self.publish_telemetry()

        # The control center already validated the route against the map.
        # Vehicles execute it tile by tile and report each reached position.
        for next_position in self.current_mission.route:
            time.sleep(1)
            self.position = {
                "x": next_position.x,
                "y": next_position.y,
            }
            print(
                f"[{self.vehicle_id}] moving to "
                f"({self.position['x']}, {self.position['y']})"
            )
            self.publish_telemetry()

    def execute_mission(self): # the classes will override this 
        raise NotImplementedError

    def is_compatible(self, request) -> bool:
        return True



def run_rpc_server(vehicle: BaseVehicle, rpc_port: int): # rpc server

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

    mission_pb2_grpc.add_VehicleServiceServicer_to_server(
        vehicle,
        server,
    )

    server.add_insecure_port(f"[::]:{rpc_port}")

    server.start()

    print(
        f"[{vehicle.vehicle_id}] "
        f"RPC server listening on port {rpc_port}"
    )

    server.wait_for_termination()
