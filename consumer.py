# consumer.py
import json
from confluent_kafka import Consumer
from language_detector import detect_and_translate
from claim_extractor import process_claim
from facts_db import load_facts, search_facts
from verifier import verify_claim, print_final_result

# Load facts once when worker starts
load_facts()

consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'fact-checker-workers',
    'enable.auto.commit': False
})
consumer.subscribe(['news-feed'])

def process_post(post):
    print(f"\n{'='*60}")
    print(f"📥 Received: {post['text'][:60]}...")

    # Step 2: Language Detection
    lang_result = detect_and_translate(post['text'])
    post['language_code'] = lang_result['language_code']
    post['language_name'] = lang_result['language_name']
    post['english_text']  = lang_result['english_text']
    print(f"   🌐 Language: {post['language_name']}")

    # Step 3: Claim Extraction
    claim_result = process_claim(post['english_text'], post['language_name'])
    post['has_claim']  = claim_result['has_claim']
    post['claim']      = claim_result['claim']
    post['claim_type'] = claim_result['claim_type']

    if not post['has_claim']:
        print(f"   ⏭️  No claim — skipping")
        return

    print(f"   ✅ Claim: {post['claim']}")

    # Step 4: Vector Search
    print(f"   🔍 Searching facts...")
    retrieved = search_facts(post['claim'], top_k=3)
    post['retrieved_facts'] = retrieved

    for r in retrieved:
        print(f"   📄 [{r['similarity']:.2f}] {r['text'][:65]}...")

    # Step 5+6: LLM Verification
    print(f"   🤖 Verifying with Claude...")
    verdict_result = verify_claim(
        post['claim'],
        post['retrieved_facts'],
        post['language_name']
    )

    post['verdict']     = verdict_result['verdict']
    post['confidence']  = verdict_result['confidence']
    post['reason']      = verdict_result['reason']

    print_final_result(post)

    # Flag high-confidence misinformation
    if post['verdict'] in ['FALSE', 'MISLEADING'] and post['confidence'] > 85:
        print(f"   🚨 ALERT: High-confidence misinformation detected!")

def run_worker():
    print("Worker started. Waiting for posts...")
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Error: {msg.error()}")
            continue

        post = json.loads(msg.value().decode('utf-8'))

        try:
            process_post(post)
            consumer.commit(msg)
            print(f"   ✓ Committed.")
        except Exception as e:
            print(f"   ✗ Failed: {e}")

if __name__ == "__main__":
    run_worker()