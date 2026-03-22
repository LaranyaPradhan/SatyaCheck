# language_detector.py
from langdetect import detect, DetectorFactory
from deep_translator import GoogleTranslator

print("Script started") 

# Makes results consistent (langdetect is random by default)
DetectorFactory.seed = 0

# Map of language codes → full names
LANGUAGE_MAP = {
    "hi": "Hindi",
    "en": "English",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ur": "Urdu",
}

HINGLISH_MARKERS = [
    "hai", "hain", "mein", "ka", "ki", "ke", "bhai", "yaar",
    "sach", "karo", "nahi", "toh", "aur", "kya", "tha", "nahi",
    "milte", "milta", "abhi", "bahut", "accha", "theek", "matlab",
    "share", "batao", "sunaa", "suno", "dekho", "isko", "usko"
]

def is_hinglish(text):
    words = text.lower().split()
    matches = sum(1 for word in words if word in HINGLISH_MARKERS)
    # If 2+ Hinglish words found → treat as Hindi
    return matches >= 2

def detect_language(text):
    try:
        if is_hinglish(text):
            return {"code": "hi", "name": "Hindi (Hinglish)", "supported": True}
        
        code = detect(text)
        name = LANGUAGE_MAP.get(code, f"Other ({code})")
        return {
            "code": code,
            "name": name,
            "supported": code in LANGUAGE_MAP
        }
    except Exception as e:
        return {
            "code": "unknown",
            "name": "Unknown",
            "supported": False
        }

def translate_to_english(text, source_lang_code):
    # Already English — skip translation
    if source_lang_code == "en":
        return text

    try:
        translated = GoogleTranslator(
            source=source_lang_code,
            target="en"
        ).translate(text)
        return translated
    except Exception as e:
        print(f"Translation failed: {e}")
        return text  # fallback: return original if translation fails

def detect_and_translate(text):
    # Step 1: detect language
    lang = detect_language(text)
    print(f"   🌐 Detected: {lang['name']} ({lang['code']})")

    # Step 2: translate to English
    english_text = translate_to_english(text, lang["code"])

    if lang["code"] != "en":
        print(f"   🔄 Translated: {english_text[:80]}...")

    return {
        "original_text": text,
        "english_text": english_text,
        "language_code": lang["code"],
        "language_name": lang["name"],
    }


# ── Test it directly ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_posts = [
        "Bhai sach mein PM KISAN mein ab 10,000 rupees milte hain!!",
        "WhatsApp has been banned in India starting next month!!",
        "சந்திரயான்-3 சந்திரனில் தரையிறங்கியது உண்மையில்லை",   # Tamil
        "ভারতে হোয়াটসঅ্যাপ নিষিদ্ধ করা হয়েছে",                 # Bengali
    ]

    for post in test_posts:
        print(f"\n📝 Original: {post[:60]}")
        result = detect_and_translate(post)
        print(f"   ✓ English: {result['english_text'][:80]}")