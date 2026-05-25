"""import socket
import json

s = socket.socket()
s.connect(("control-center", 8080))

payload = {
    "id": "boat-1",
    "unit": "vehicle",
    "vehicle_type": "boat",
    "position": {
        "x": 1,
        "y": 1
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


class BoatVehicle(BaseVehicle):

    def __init__(self, vehicle_id, position):

        super().__init__(
            vehicle_id=vehicle_id,
            vehicle_type="boat",
        )

        self.position = position

    
    def is_compatible(self, request) -> bool:

        return (
            request.area_type == mission_pb2.WATER # only  water alerts for boats 
        )

    
    def execute_mission(self):
        # remaining : simulate the position of the vehicle to the incident position
        try:

            print(
                f"[{self.vehicle_id}] "
                f"starting water mission"
            )

            self.state = mission_pb2.BUSY

            # navigation
            for progress in [10, 20, 30]:

                time.sleep(1)

                self.progress = progress

                print(
                    f"[{self.vehicle_id}] "
                    f"navigating water route "
                    f"{self.progress}%"
                )

            # monitoring
            for progress in [45, 60, 75]:

                time.sleep(1)

                self.progress = progress

                print(
                    f"[{self.vehicle_id}] "
                    f"monitoring water level "
                    f"{self.progress}%"
                )

           
            for progress in [90, 100]:

                time.sleep(1)

                self.progress = progress

                print(
                    f"[{self.vehicle_id}] "
                    f"stabilizing flood zone "
                    f"{self.progress}%"
                )

            self.state = mission_pb2.COMPLETED

            self.result_message = (
                "Water mission completed successfully"
            )

            print(
                f"[{self.vehicle_id}] "
                f"mission completed"
            )

            
            time.sleep(2) # reset

            self.state = mission_pb2.IDLE
            self.progress = 0
            self.current_mission = None

        except Exception as error:

            self.state = mission_pb2.ERROR

            self.result_message = str(error)

            print(
                f"[{self.vehicle_id}] ERROR: {error}"
            )



def register_vehicle( # registration
    vehicle_id: str,
    rpc_host: str,
    rpc_port: int,
    position: dict,
):

    payload = {
        "id": vehicle_id,
        "unit": "vehicle",
        "vehicle_type": "boat",
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

    VEHICLE_ID = "boat-1"

    RPC_HOST = "vehicle-boat"
    RPC_PORT = 50053

    POSITION = {
        "x": 12,
        "y": 8,
    }

    
    register_vehicle( # register
        vehicle_id=VEHICLE_ID,
        rpc_host=RPC_HOST,
        rpc_port=RPC_PORT,
        position=POSITION,
    )

    
    vehicle = BoatVehicle( # create vehicle
        vehicle_id=VEHICLE_ID,
        position=POSITION,
    )

    
    run_rpc_server( # start the rpc
        vehicle=vehicle,
        rpc_port=RPC_PORT,
    )