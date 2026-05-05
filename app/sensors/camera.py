import socket
import json
import random
import time

s = socket.socket()
s.connect(("control-center", 8080))

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

s.send(request.encode())
print(s.recv(4096).decode())

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

        s.send(incident_request.encode())
        incident_counter = incident_counter + 1

    time.sleep(5)