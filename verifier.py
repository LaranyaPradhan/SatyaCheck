# verifier.py
import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def format_facts_for_prompt(retrieved_facts):
    """Format the retrieved facts into a clean string for the prompt."""
    if not retrieved_facts:
        return "No relevant facts found in database."
    
    lines = []
    for i, fact in enumerate(retrieved_facts, 1):
        lines.append(f"{i}. {fact['text']}")
        lines.append(f"   Source: {fact['source']} | Similarity: {fact['similarity']}")
    
    return "\n".join(lines)


def verify_claim(claim, retrieved_facts, original_language="English"):
    """
    Send the claim + retrieved facts to Claude for final verdict.
    Returns: dict with verdict, confidence, reason
    """

    facts_text = format_facts_for_prompt(retrieved_facts)

    prompt = f"""You are a professional fact-checker for Indian news and social media.

CLAIM TO VERIFY:
{claim}

VERIFIED FACTS FROM DATABASE:
{facts_text}

Based ONLY on the verified facts above, classify the claim as one of:
- TRUE: the claim matches the verified facts
- FALSE: the claim directly contradicts the verified facts  
- MISLEADING: the claim is partially true but framing or numbers are wrong
- UNVERIFIABLE: the facts database doesn't have enough info to judge

Respond ONLY in this exact JSON format, no explanation outside it:
{{
  "verdict": "TRUE/FALSE/MISLEADING/UNVERIFIABLE",
  "confidence": <number 0-100>,
  "reason": "one sentence explaining why, in {original_language} if possible"
}}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except:
        return {
            "verdict": "UNVERIFIABLE",
            "confidence": 0,
            "reason": "Could not parse verdict."
        }


def print_final_result(post):
    """Print the complete fact-check result cleanly."""
    verdict = post.get("verdict", "UNVERIFIABLE")
    confidence = post.get("confidence", 0)
    reason = post.get("reason", "")

    emoji = {
        "TRUE": "✅",
        "FALSE": "❌",
        "MISLEADING": "⚠️",
        "UNVERIFIABLE": "❓"
    }.get(verdict, "❓")

    print(f"\n{'='*60}")
    print(f"   {emoji} VERDICT: {verdict} (Confidence: {confidence}%)")
    print(f"   💬 Reason: {reason}")
    print(f"{'='*60}")


# ── Test it directly ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Simulated test — as if Steps 1-4 already ran
    test_cases = [
        {
            "claim": "PM KISAN gives Rs 10,000 per year to farmers",
            "retrieved_facts": [
                {
                    "text": "PM-KISAN scheme provides Rs 6000 per year to eligible farmers in three equal instalments of Rs 2000.",
                    "source": "pib.gov.in",
                    "similarity": 0.91
                }
            ],
            "language": "Hindi"
        },
        {
            "claim": "WhatsApp has been banned in India",
            "retrieved_facts": [
                {
                    "text": "WhatsApp is not banned in India. It continues to operate normally as of 2024.",
                    "source": "meity.gov.in",
                    "similarity": 0.94
                }
            ],
            "language": "English"
        },
        {
            "claim": "Chandrayaan-3 never landed on the moon",
            "retrieved_facts": [
                {
                    "text": "Chandrayaan-3 successfully landed on the Moon's south pole on August 23, 2023.",
                    "source": "isro.gov.in",
                    "similarity": 0.89
                }
            ],
            "language": "Tamil"
        },
    ]

    for case in test_cases:
        print(f"\n🔍 Claim: {case['claim']}")
        result = verify_claim(case["claim"], case["retrieved_facts"], case["language"])
        print(f"   Verdict: {result['verdict']}")
        print(f"   Confidence: {result['confidence']}%")
        print(f"   Reason: {result['reason']}")