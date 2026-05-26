"""import socket
import json

s = socket.socket()
s.connect(("control-center", 8080))

payload = {
    "id": "rover-1",
    "unit": "vehicle",
    "vehicle_type": "rover",
    "position": {
        "x": 8,
        "y": 15
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


class RoverVehicle(BaseVehicle):

    def __init__(self, vehicle_id, position):

        super().__init__(
            vehicle_id=vehicle_id,
            vehicle_type="rover",
        )

        self.position = position

    
    def is_compatible(self, request) -> bool:

        return (
            request.incident_type == "vibration_alert"
            or (
                request.incident_type == "person_detected"
                and request.area_type == mission_pb2.LAND
            )
        )

    
    def execute_mission(self):
        # simulate travel
        try:

            print(
                f"[{self.vehicle_id}] "
                f"starting repair mission"
            )

            self.state = mission_pb2.BUSY

            
            for progress in [10, 20, 30, 40]:

                time.sleep(1)

                self.progress = progress

                print(
                    f"[{self.vehicle_id}] "
                    f"driving to location "
                    f"{self.progress}%"
                )

           
            for progress in [55, 70]:

                time.sleep(1)

                self.progress = progress

                print(
                    f"[{self.vehicle_id}] "
                    f"inspecting damage "
                    f"{self.progress}%"
                )

            
            for progress in [85, 100]:

                time.sleep(1)

                self.progress = progress

                print(
                    f"[{self.vehicle_id}] "
                    f"repairing structure "
                    f"{self.progress}%"
                )

            self.state = mission_pb2.COMPLETED

            if self.current_mission.incident_type == "person_detected":
                self.result_message = "Land rescue mission completed"
            else:
                self.result_message = "Repair mission completed"

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



def register_vehicle( # register on the control centre with  REST
    vehicle_id: str,
    rpc_host: str,
    rpc_port: int,
    position: dict,
):

    payload = {
        "id": vehicle_id,
        "unit": "vehicle",
        "vehicle_type": "rover",
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

    VEHICLE_ID = "rover-1"

    RPC_HOST = "vehicle-rover"
    RPC_PORT = 50052

    POSITION = {
        "x": 8,
        "y": 15,
    }

    register_vehicle(
        vehicle_id=VEHICLE_ID,
        rpc_host=RPC_HOST,
        rpc_port=RPC_PORT,
        position=POSITION,
    )

    vehicle = RoverVehicle(
        vehicle_id=VEHICLE_ID,
        position=POSITION,
    )

    run_rpc_server(
        vehicle=vehicle,
        rpc_port=RPC_PORT,
    )
