"""import socket
import json

s = socket.socket()
s.connect(("control-center", 8080))

payload = {
    "id": "drone-1",
    "unit": "vehicle",
    "vehicle_type": "drone",
    "position": {
        "x": 5,
        "y": 12
    }
}

body = json.dumps(payload)

request = (
    "POST /unit HTTP/1.1\r\n"
    "Host: control-center\r\n"
    "Content-Type: application/json\r\n"
    f"Content-Length: {len(body.encode())}\r\n"
    "\r\n"
    + body
)

s.send(request.encode())
print(s.recv(4096).decode())"""

import json
import socket
import time

from app.vehicles.rpc_server import (
    BaseVehicle,
    run_rpc_server,
)

from app.rpc.generated import mission_pb2


class DroneVehicle(BaseVehicle):

    def __init__(self, vehicle_id, position):

        super().__init__(
            vehicle_id=vehicle_id,
            vehicle_type="drone",
        )

        self.position = position

    
    def is_compatible(self, request) -> bool:

        return (
            request.incident_type == "water_level_alert"
        )

    
    def execute_mission(self):
        # simulate travel remaining 
        try:

            print(
                f"[{self.vehicle_id}] "
                f"starting aerial mission"
            )

            self.state = mission_pb2.BUSY

            
            for progress in [10, 20]:

                time.sleep(1)

                self.progress = progress

                print(
                    f"[{self.vehicle_id}] "
                    f"taking off "
                    f"{self.progress}%"
                )

            
            for progress in [35, 50, 65]:

                time.sleep(1)

                self.progress = progress

                print(
                    f"[{self.vehicle_id}] "
                    f"flying to target "
                    f"{self.progress}%"
                )

            
            for progress in [80, 90, 100]:

                time.sleep(1)

                self.progress = progress

                print(
                    f"[{self.vehicle_id}] "
                    f"scanning area "
                    f"{self.progress}%"
                )

            self.state = mission_pb2.COMPLETED

            self.result_message = (
                "Water level alert inspection completed"
            )

            print(
                f"[{self.vehicle_id}] "
                f"mission completed"
            )

            time.sleep(2)

            self.state = mission_pb2.IDLE
            self.progress = 0
            self.current_mission = None

        except Exception as error:

            self.state = mission_pb2.ERROR

            self.result_message = str(error)

            print(
                f"[{self.vehicle_id}] ERROR: {error}"
            )



def register_vehicle( # register at the control center using REST
    vehicle_id: str,
    rpc_host: str,
    rpc_port: int,
    position: dict,
):

    payload = {
        "id": vehicle_id,
        "unit": "vehicle",
        "vehicle_type": "drone",
        "rpc_host": rpc_host,
        "rpc_port": rpc_port,
        "position": {
            "x": position["x"],
            "y": position["y"],
        },
    }

    body = json.dumps(payload)

    request = (
        "POST /unit HTTP/1.1\r\n"
        "Host: control-center\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body.encode())}\r\n"
        "\r\n"
        + body
    )

    client = socket.socket()

    client.connect(("control-center", 8080))

    client.send(request.encode())

    response = client.recv(4096).decode()

    print(response)

    client.close()



if __name__ == "__main__":

    VEHICLE_ID = "drone-1"

    RPC_HOST = "vehicle-drone"
    RPC_PORT = 50051

    POSITION = {
        "x": 5,
        "y": 12,
    }

    register_vehicle(
        vehicle_id=VEHICLE_ID,
        rpc_host=RPC_HOST,
        rpc_port=RPC_PORT,
        position=POSITION,
    )

    vehicle = DroneVehicle(
        vehicle_id=VEHICLE_ID,
        position=POSITION,
    )

    run_rpc_server(
        vehicle=vehicle,
        rpc_port=RPC_PORT,
    )
