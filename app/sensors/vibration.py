import socket
import json
import random
import time

s = socket.socket()
s.connect(("control-center", 8080))

payload = {
    "id": "vibration-1",
    "unit": "sensor",
    "sensor_type": "vibration",
    "position": {
        "x": 15,
        "y": 18
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
print(s.recv(4096).decode())

incident_counter = 0

while True:

    vibration_index = random.randint(0, 100)

    print(f"Measured Vibration level: {vibration_index}")


    if vibration_index > 80:

        incident_payload = {
            "id": f"vibration-1-incident-{incident_counter}",
            "incident_type": "vibration_alert",
            "source_id": "vibration-1",
            "message": f"High Vibration Detected: {vibration_index}",
            "position": {
                "x": 15,
                "y": 18
            },
            "priority": 2,
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

        s.send(incident_request.encode())
        incident_counter = incident_counter + 1 

    time.sleep(5)