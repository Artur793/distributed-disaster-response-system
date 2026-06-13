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
        self.mqtt_client = None

    
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
        self.mqtt_client = connect_mqtt_client(client_id=self.vehicle_id)
        self.publish_telemetry()

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
