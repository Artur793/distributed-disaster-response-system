import json
import time
from datetime import datetime, timezone
from itertools import count
from threading import Lock

import paho.mqtt.client as mqtt


MQTT_VERSION = "1.0"
DEFAULT_BROKER_HOST = "mosquitto"
DEFAULT_BROKER_PORT = 1883
DEFAULT_KEEPALIVE_SECONDS = 60
DEFAULT_RETRY_SECONDS = 5


class MessageIdGenerator:
    def __init__(self):
        self._counter = count(1)
        self._lock = Lock()

    def next(self, source_id: str) -> str:
        with self._lock:
            sequence = next(self._counter)
        timestamp_ms = int(time.time() * 1000)
        return f"{source_id}-{timestamp_ms}-{sequence}"


def utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def message_envelope(
    publisher_id: str,
    message_ids: MessageIdGenerator,
) -> dict:
    return {
        "version": MQTT_VERSION,
        "message_id": message_ids.next(publisher_id),
        "timestamp": utc_timestamp(),
    }


def connect_mqtt_client(
    client_id: str,
    *,
    host: str = DEFAULT_BROKER_HOST,
    port: int = DEFAULT_BROKER_PORT,
    keepalive: int = DEFAULT_KEEPALIVE_SECONDS,
    retry_seconds: int = DEFAULT_RETRY_SECONDS,
    will_topic: str | None = None,
    will_payload: dict | None = None,
    will_qos: int = 1,
) -> mqtt.Client:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
    )
    client.reconnect_delay_set(
        min_delay=retry_seconds,
        max_delay=30,
    )

    if will_topic is not None and will_payload is not None:
        client.will_set(
            will_topic,
            payload=json.dumps(will_payload),
            qos=will_qos,
            retain=False,
        )

    while True:
        try:
            client.connect(host, port, keepalive)
            break
        except OSError as error:
            print(
                f"MQTT broker unavailable for {client_id} "
                f"({error}); retrying in {retry_seconds}s"
            )
            time.sleep(retry_seconds)

    client.loop_start()
    return client


def publish_json(
    client: mqtt.Client,
    topic: str,
    payload: dict,
    *,
    qos: int,
    wait_for_publish: bool = False,
    retry_seconds: int = DEFAULT_RETRY_SECONDS,
) -> mqtt.MQTTMessageInfo:
    encoded_payload = json.dumps(payload)

    while True:
        message_info = client.publish(
            topic,
            payload=encoded_payload,
            qos=qos,
            retain=False,
        )
        if not wait_for_publish:
            return message_info

        try:
            message_info.wait_for_publish()
            return message_info
        except RuntimeError as error:
            print(
                f"MQTT publish to {topic} failed ({error}); "
                f"retrying in {retry_seconds}s"
            )
            time.sleep(retry_seconds)
