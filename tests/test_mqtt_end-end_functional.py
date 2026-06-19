import json
import time
import uuid

import paho.mqtt.client as mqtt


def test_publish_500_events():
    """
    Publish 500 MQTT events to the running broker.
    """

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect("localhost", 1883, 60)

    start = time.perf_counter()

    for i in range(500):
        payload = {
            "message_id": str(uuid.uuid4()),
            "timestamp": "2026-06-17T12:00:00Z",
            "id": f"incident-{i}",
            "incident_type": "water_level_alert",
            "source_id": "sensor-load",
            "message": "Load test",
            "position": {
                "x": i % 20,
                "y": (i * 3) % 20,
            },
        }

        result =  client.publish(
            "island/events/load",
            json.dumps(payload),
            qos=0,
        )
        result.wait_for_publish()

        assert result.rc == mqtt.MQTT_ERR_SUCCESS

    client.loop()

    elapsed = time.perf_counter() - start

    print(f"Published 500 events in {elapsed:.3f} s")

    assert elapsed < 5



