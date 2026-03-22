# SatyaCheck 
### Scalable Automated Fact-Checker for Vernacular Indian News

An end-to-end AI-powered misinformation detection pipeline built for Indian languages. Ingests social media posts, detects language, extracts verifiable claims, and returns a TRUE / FALSE / MISLEADING verdict with confidence score and reasoning.

---

## Pipeline Architecture
```
Social Media Posts
      ↓
[ Apache Kafka ]           → Step 1: Message queue, handles thousands of posts/min
      ↓
[ Language Detector ]      → Step 2: Detects Hindi, Hinglish, Tamil, Bengali, etc.
      ↓
[ Claim Extractor ]        → Step 3: Strips fluff, extracts clean factual claim (Claude Haiku)
      ↓
[ ChromaDB Vector Search ] → Step 4: Finds relevant verified facts via semantic search
      ↓
[ LLM Verifier ]           → Step 5+6: Claude gives final verdict with confidence score
  
```

## Supported Languages

Tested: Hindi (Hinglish) · Tamil · Bengali · English
Supported via langdetect + Google Translate: Telugu · Marathi · Gujarati · Kannada · Malayalam · Punjabi · Urdu

---

##  Tech Stack

```
Component              Technology
─────────────────────────────────────────────────────────
Message Queue        │ Apache Kafka (KRaft mode via Docker)
Language Detection   │ langdetect + custom Hinglish detector
Translation          │ Google Translate (deep-translator)
Claim Extraction     │ Claude Haiku API
Vector Database      │ ChromaDB (local persistent)
Embeddings           │ paraphrase-multilingual-MiniLM-L12-v2
LLM Verification     │ Claude Haiku API
```

## Project Structure
```
vernacular/
├── producer.py           # Ingests posts into Kafka
├── consumer.py           # Worker: runs full pipeline per post
├── language_detector.py  # Step 2: language detection + translation
├── claim_extractor.py    # Step 3: rule filter + Claude claim extraction
├── facts_db.py           # Step 4: ChromaDB vector search
├── verifier.py           # Step 5+6: LLM verdict
├── docker-compose.yml    # Kafka setup
├── .env                  # API keys (never pushed to GitHub)
└── chroma_db/            # Local vector database (auto-created)
```

## Setup & Running

### 1. Clone the repo
git clone https://github.com/yourusername/satyacheck.git
cd satyacheck

### 2. Create virtual environment
python -m venv vernac
vernac\Scripts\activate      # Windows
source vernac/bin/activate   # Mac/Linux

### 3. Install dependencies
pip install confluent-kafka anthropic python-dotenv langdetect deep-translator chromadb sentence-transformers

### 4. Add your API key
Create a .env file in the project root:
ANTHROPIC_API_KEY=sk-ant-your-key-here

### 5. Start Kafka
docker compose up -d

### 6. Run the pipeline

Terminal 1 — start the worker:
python consumer.py

Terminal 2 — send test posts:
python producer.py

---

## Key Design Decisions

**Hinglish Detection** — langdetect struggles with Roman-script Hindi. A custom keyword matcher detects Hinglish before langdetect runs.

**Two-stage Claim Extraction** — a rule-based fast filter drops ~30% of posts instantly before any API call, reducing cost and latency.

**Multilingual Embeddings** — uses paraphrase-multilingual-MiniLM-L12-v2 instead of English-only models, so vector search works across all Indian languages.

**Recency-aware Retrieval** — the facts database stores dates so outdated facts can be filtered out in production.

---

## Scalability

- Kafka absorbs traffic spikes without data loss
- Run 50 parallel workers with multiprocessing.Pool
- Redis caching prevents re-verifying the same viral rumor
- Only ~50% of posts reach the LLM after filtering

---
