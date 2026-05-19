import socket
import time
import json
import threading

HOST = "127.0.0.1"
PORT = 8080

# first have to start docker container for control-center

def send_get_status_request(): # from connecting to recieving the request

    request = (
        "GET /status HTTP/1.1\r\n"
        "Host: localhost\r\n"
        "\r\n"
    )

    s = socket.socket()
    s.connect((HOST, PORT))

    s.sendall(request.encode())
    
    response = s.recv(4096)

    s.close()

    return response

def send_post_incident_request():    # from connecting to recieving the request
    global counter 
    incident_payload = {
            "id": f"camera-1-incident-{6}", # change the id evrytime , because only one incident id can be registered 
            "incident_type": "person_detected",
            "source_id": "camera-1",
            "message": f"Person Detected with High-Probability: {80}",
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

    s = socket.socket()
    s.connect((HOST, PORT))

    s.sendall(incident_request.encode())
    
    
    response = s.recv(4096)

    s.close()

    return response


def test_get_status_latency():
    start = time.perf_counter()

    a = send_get_status_request()

    end = time.perf_counter()

    #print(a)

    latency_ms = (end - start) * 1000  # difference between start time and end time

    print(f"GET_STATUS_LATENCY: {latency_ms:.2f} ms") 

    assert latency_ms < 100  

def test_average_get_status_latency():

    latencies = []

    for _ in range(20):

        start = time.perf_counter()

        send_get_status_request()

        end = time.perf_counter()

        latency_ms = (end - start) * 1000 # difference between start time and end time

        latencies.append(latency_ms)

    average = sum(latencies) / len(latencies) # average

    print(f"GET_STATUS_AVERAGE_LATENCY: {average:.2f} ms")

    assert average < 100


def test_post_incident_latency():
    start = time.perf_counter()

    a = send_post_incident_request()

    end = time.perf_counter()

    print(a)

    latency_ms = (end - start) * 1000

    print(f"POST_INCIDENT_LATENCY: {latency_ms:.2f} ms")

    assert latency_ms < 100

def test_average_post_incident_latency():

    latencies = []

    for _ in range(20):

        start = time.perf_counter()

        send_post_incident_request()

        end = time.perf_counter()

        latency_ms = (end - start) * 1000

        latencies.append(latency_ms)

    average = sum(latencies) / len(latencies)

    print(f"POST_INCIDENT_AVERAGE_LATENCY: {average:.2f} ms")

    assert average < 100


def test_concurrent_request_latency():    # for fifty concurrent requests 
    results = []
    
    def worker():
        start = time.perf_counter()
        send_get_status_request()
        end = time.perf_counter()
        results.append((end - start) * 1000)
    
    threads = [threading.Thread(target=worker) for _ in range(10)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    print(f"CONCURRENT_AVG_LATENCY: {sum(results)/len(results):.2f} ms")
    print(f"CONCURRENT_MAX_LATENCY: {max(results):.2f} ms")

def test_burst_latency():         # for fast 50 requests 
    latencies = []
    for _ in range(50):
        start = time.perf_counter()
        send_get_status_request()
        latencies.append((time.perf_counter() - start) * 1000)
    
    print(f"Die Hälfte der requests: {sorted(latencies)[25]:.2f} ms")
    print(f"99% der requests: {sorted(latencies)[49]:.2f} ms")

