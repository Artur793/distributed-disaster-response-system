import socket
import json
import random
import time

CONTROL_CENTER_ADDRESS = ("control-center", 8080)
REGISTRATION_RETRY_SECONDS = 3


def send_request(request: str) -> str:
    # The REST server closes the connection after each response; sensors open
    # a new socket for each registration or incident report.
    with socket.create_connection(CONTROL_CENTER_ADDRESS) as client:
        client.sendall(request.encode())
        chunks = []
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
    return b"".join(chunks).decode()


def register_sensor(request: str) -> None:
    while True:
        try:
            response = send_request(request)
        except OSError as error:
            print(f"Camera registration failed: {error}. Retrying...")
            time.sleep(REGISTRATION_RETRY_SECONDS)
            continue

        print(response)
        # A 409 means this known sensor is already recorded after reconnecting.
        if response.startswith("HTTP/1.1 201") or response.startswith("HTTP/1.1 409"):
            return

        print("Camera registration rejected. Retrying...")
        time.sleep(REGISTRATION_RETRY_SECONDS)

payload = {
    "id": "camera-1",
    "unit": "sensor",
    "sensor_type": "camera",
    "position": {
        "x": 10,
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

register_sensor(request)

incident_counter = 0

while True:

    person_confidence = random.randint(0, 100)

    print(f"Person Detected Probability: {person_confidence}")


    if person_confidence > 80:

        incident_payload = {
            "id": f"camera-1-incident-{incident_counter}",
            "incident_type": "person_detected",
            "source_id": "camera-1",
            "message": f"Person Detected with High-Probability: {person_confidence}",
            "position": {
                "x": 10,
                "y": 12
            },
            "priority": 1,
            "status": "open"
        }

        incident_body = json.dumps(incident_payload)

        incident_request = (
            "POST /incident HTTP/1.1\r\n"
            "Host: control-center\r\n"
            "Content-Type: application/json\r\n"
            f"Content-Length: {len(incident_body.encode())}\r\n"
            "\r\n"
            + incident_body
        )

        try:
            print(send_request(incident_request))
        except OSError as error:
            print(f"Camera incident report failed: {error}")
        incident_counter = incident_counter + 1

    time.sleep(5)
