# claim_extractor.py
print("Script started")
import os
import json
import requests
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

SCALEDOWN_API_KEY = os.getenv("SCALEDOWN_API_KEY")
SCALEDOWN_URL = "https://api.scaledown.xyz/compress/raw/"
SCALEDOWN_HEADERS = {
    "x-api-key": SCALEDOWN_API_KEY,
    "Content-Type": "application/json"
}

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def compress_with_scaledown(text):
    """
    ScaleDown works well for long text (100+ tokens).
    For short social media posts, skip it — nothing to compress.
    """
    word_count = len(text.split())

    if word_count < 50:
        print(f"   ⏭️  ScaleDown skipped (post too short: {word_count} words)")
        return text

    payload = {
        "context": "Extract the core factual claim. Remove slang, emojis, urgency words, greetings, and opinions.",
        "prompt": text,
        "scaledown": {"rate": "auto"}
    }
    try:
        response = requests.post(SCALEDOWN_URL, headers=SCALEDOWN_HEADERS, data=json.dumps(payload))
        result = response.json()
        inner = result.get("results", {})

        if inner.get("success"):
            compressed = inner["compressed_prompt"]

            # Safety check: if ScaleDown returned the context string, use original
            if "factual claim" in compressed.lower() or len(compressed) < 10:
                print(f"   ⚠️  ScaleDown over-compressed, using original")
                return text

            original_tokens = inner["original_prompt_tokens"]
            compressed_tokens = inner["compressed_prompt_tokens"]
            savings = round((1 - compressed_tokens / original_tokens) * 100)
            print(f"   ✂️  ScaleDown: {original_tokens} → {compressed_tokens} tokens ({savings}% saved)")
            return compressed
        else:
            return text
    except Exception as e:
        print(f"   ⚠️  ScaleDown error: {e}")
        return text


def extract_claim_with_groq(text, original_language):
    prompt = f"""Extract the single verifiable factual claim from this social media post originally in {original_language}.
Return ONLY valid JSON, no markdown, no explanation:
{{"has_claim": true/false, "claim": "one clean factual sentence or empty string", "claim_type": "statistic|event|policy|person|other"}}

Post: {text}"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"   ⚠️  Groq error: {e}")
        return {"has_claim": False, "claim": "", "claim_type": "unknown"}


def process_claim(english_text, original_language="English"):
    print(f"   📝 Original:   {english_text[:70]}...")

    # Stage A: ScaleDown (only useful for long text)
    compressed = compress_with_scaledown(english_text)
    print(f"   🗜️  To verify:  {compressed[:70]}...")

    # Stage B: Groq extraction
    result = extract_claim_with_groq(compressed, original_language)

    if result["has_claim"]:
        print(f"   ✅ Claim: {result['claim']}")
        print(f"   🏷️  Type:  {result['claim_type']}")
    else:
        print(f"   ⏭️  No verifiable claim found")

    return result


if __name__ == "__main__":
    test_posts = [
        {"text": "Brother, it is true that PM KISAN now gives Rs 10,000 per year to farmers!!", "lang": "Hindi"},
        {"text": "WhatsApp has been completely banned in India starting next month share this everyone!!", "lang": "English"},
        {"text": "It is not true that Chandrayaan-3 landed on the moon", "lang": "Tamil"},
        {"text": "Good morning everyone have a great day!!", "lang": "English"},
    ]

    for post in test_posts:
        print(f"\n{'─'*60}")
        result = process_claim(post["text"], post["lang"])