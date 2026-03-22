# producer.py
import json          
import hashlib       
import time          
from confluent_kafka import Producer

producer = Producer({'bootstrap.servers': 'localhost:9092'})

def ingest_post(raw_text):
    message = {
        "id": hashlib.md5(f"{raw_text}{time.time()}".encode()).hexdigest(),  # real unique ID
        "text": raw_text,
        "source": "twitter",
        "timestamp": time.time()
    }
    producer.produce(
        topic='news-feed',
        value=json.dumps(message, ensure_ascii=False).encode('utf-8')
    )
    producer.flush()
    print(f"✓ Sent: {raw_text[:50]}...")

if __name__ == "__main__":
    ingest_post("Bhai sach mein PM KISAN mein ab 10,000 rupees milte hain!!")
    ingest_post("WhatsApp has been banned in India starting next month!!")
    ingest_post("Chandrayaan-3 never actually landed on the moon, ISRO lied")
    print("All posts sent to Kafka.")