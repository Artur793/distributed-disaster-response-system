import time
from unittest.mock import MagicMock

from app.common.mqtt_publisher import publish_json

from app.common.mqtt_publisher import (
    MessageIdGenerator,
    message_envelope,
)
import json

from app.control_center.mqtt_subscriber import MQTTSubscriber
from app.common.state import SystemState


def test_envelope_generation_speed():
    gen = MessageIdGenerator()

    start = time.perf_counter()

    for _ in range(10000):
        message_envelope("sensor-1", gen)

    elapsed = time.perf_counter() - start

    assert elapsed < 1.0

def test_publish_json_calls_client_once():
    client = MagicMock()

    publish_json(
        client,
        "island/events/test",
        {"hello": "world"},
        qos=1,
    )

    client.publish.assert_called_once()


def test_mqtt_processing_latency():
    

    #Measures the time from receiving an MQTT message until it has been processed by the subscriber.


    state = SystemState()
    subscriber = MQTTSubscriber(state)

    payload = {
        "message_id": "latency-test",
        "timestamp": "2099-01-01T00:00:00Z",
        "id": "inc-lat",
        "incident_type": "person_detected",
        "source_id": "camera-1",
        "message": "Person detected",
        "position": {
            "x": 3,
            "y": 7,
        },
    }

    msg = MagicMock()
    msg.topic = "island/events/person"
    msg.payload = json.dumps(payload).encode()

    start = time.perf_counter()
    before = len(subscriber.processed_message_ids)
    subscriber.on_message(None, None, msg)
    assert len(subscriber.processed_message_ids) == before +1 

    elapsed_ms = (time.perf_counter() - start) * 1000

    print(f"MQTT processing latency: {elapsed_ms:.3f} ms")

    # Local processing should be comfortably below 50 ms.
    assert elapsed_ms < 50



def test_process_1000_messages():
   
    #Verifies that the subscriber can process many MQTT messages quickly without crashing.
    

    state = SystemState()
    subscriber = MQTTSubscriber(state)

    start = time.perf_counter()

    for i in range(1000):
        payload = {
            "message_id": f"id-{i}",
            "timestamp": "2099-01-01T00:00:00Z",
            "id": f"inc-{i}",
            "incident_type": "water_level_alert",
            "source_id": "sensor",
            "message": "event",
            "position": {
                "x": i % 20,
                "y": i % 20,
            },
        }

        msg = MagicMock()
        msg.topic = "island/events/test"
        msg.payload = json.dumps(payload).encode()

        subscriber.on_message(None, None, msg)

    elapsed = time.perf_counter() - start

    print(f"Processed 1000 messages in {elapsed:.3f} seconds")

    assert len(subscriber.processed_message_ids) >= 1000
    assert elapsed < 2.0