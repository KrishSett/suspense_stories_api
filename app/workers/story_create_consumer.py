# story_create_consumer.py
from kafka import KafkaConsumer
import json
from app.jobs import download_audio_and_get_info

KAFKA_BROKER_URL = "localhost:9092"
AUDIO_STORY_TOPIC = "audio_story_create"

consumer = KafkaConsumer(
    AUDIO_STORY_TOPIC,
    bootstrap_servers=KAFKA_BROKER_URL,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="audio_story_group"
)

def story_processor():
    for message in consumer:
        data = message.value
        download_audio_and_get_info(data)
