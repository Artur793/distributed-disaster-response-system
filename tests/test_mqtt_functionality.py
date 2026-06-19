import json
from unittest.mock import MagicMock

from app.control_center.mqtt_subscriber import MQTTSubscriber
from app.common.state import SystemState


def test_duplicate_message_id_is_ignored():
    state = SystemState()
    subscriber = MQTTSubscriber(state)

    payload = {
        "message_id": "dup-1",
        "timestamp": "2099-01-01T00:00:00Z",
        "id": "inc-1",
        "incident_type": "water_level_alert",
        "source_id": "sensor-1",
        "message": "alarm",
        "position": {"x": 1, "y": 1},
    }

    msg = MagicMock()
    msg.topic = "island/events/test"
    msg.payload = json.dumps(payload).encode()

    subscriber.on_message(None, None, msg)
    processed_before = len(subscriber.processed_message_ids)

    subscriber.on_message(None, None, msg)

    assert len(subscriber.processed_message_ids) == processed_before

def test_old_message_is_rejected():
    state = SystemState()
    subscriber = MQTTSubscriber(state)

    payload = {
        "message_id": "old-msg",
        "timestamp": "2020-01-01T00:00:00Z",
        "id": "inc-old",
        "incident_type": "water_level_alert",
        "source_id": "sensor-1",
        "message": "old",
        "position": {"x": 2, "y": 2},
    }

    msg = MagicMock()
    msg.topic = "island/events/test"
    msg.payload = json.dumps(payload).encode()

    before = len(subscriber.processed_message_ids)

    subscriber.on_message(None, None, msg)

    assert len(subscriber.processed_message_ids) == before

def test_on_connect_subscribes_to_required_topics():
    state = SystemState()
    subscriber = MQTTSubscriber(state)

    fake_client = subscriber.client
    fake_client.subscribe = lambda *args, **kwargs: calls.append(args)

    global calls
    calls = []

    subscriber.on_connect(fake_client, None, None, None, None)

    topics = [c[0] for c in calls]

    assert "island/events/#" in topics
    assert "island/telemetry/#" in topics
    assert "island/status/#" in topics




def test_complete_mqtt_workflow():
    

    state = SystemState()
    subscriber = MQTTSubscriber(state)

    #Incident Event 

    incident_payload = {
        "message_id": "workflow-1",
        "timestamp": "2099-01-01T00:00:00Z",
        "id": "incident-42",
        "incident_type": "water_level_alert",
        "source_id": "sensor-01",
        "message": "High water level",
        "position": {
            "x": 10,
            "y": 15,
        },
    }

    msg = MagicMock()
    msg.topic = "island/events/water"
    msg.payload = json.dumps(incident_payload).encode()
    before = len(subscriber.processed_message_ids)

    subscriber.on_message(None, None, msg)

    after = len(subscriber.processed_message_ids)

    assert after == before + 1
    subscriber.on_message(None, None, msg)

    #assert "workflow-1" in subscriber.processed_message_ids

    # Vehicle Tele

    telemetry_payload = {
        "vehicle_id": "drone-1",
        "position": {
            "x": 10,
            "y": 15,
        },
        "status": "BUSY",
        "progress": 50,
    }

    msg2 = MagicMock()
    msg2.topic = "island/telemetry/drone-1"
    msg2.payload = json.dumps(telemetry_payload).encode()

    subscriber.on_message(None, None, msg2)

    # Subscriber should process without exception
    #assert True
    #assert "workflow-1" in subscriber.processed_message_ids
    assert len(subscriber.processed_message_ids) == 1
    
    