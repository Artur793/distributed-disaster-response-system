import socket
import json
import random
import time

s = socket.socket()
s.connect(("control-center", 8080))

payload = {
    "id": "water-1",
    "unit": "sensor",
    "sensor_type": "water",
    "position": {
        "x": 1,
        "y": 2
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

    water_level_cm = random.randint(0, 100)

    print(f"Measured water level: {water_level_cm}")


    if water_level_cm > 80:

        incident_payload = {
            "id": f"water-1-incident-{incident_counter}",
            "incident_type": "water_level_alert",
            "source_id": "water-1",
            "message": f"Critical water level detected: {water_level_cm}",
            "position": {
                "x": 1,
                "y": 2
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