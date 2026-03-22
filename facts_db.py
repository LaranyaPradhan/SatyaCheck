# facts_db.py
import chromadb
from chromadb.utils import embedding_functions

# ── Setup ChromaDB (runs locally, no server needed) ──────────────────────────
client = chromadb.PersistentClient(path="./chroma_db")  # saves to disk

# Use a multilingual embedding model — handles Hindi, Tamil, etc.
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
    # This model understands 50+ languages including all major Indian ones
)

collection = client.get_or_create_collection(
    name="verified_facts",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}  # cosine similarity for text
)


# ── Verified Facts (from PIB, AltNews, BOOM, ISRO, RBI) ──────────────────────
VERIFIED_FACTS = [
    {
        "id": "fact_001",
        "text": "PM-KISAN scheme provides Rs 6000 per year to eligible farmers in three equal instalments of Rs 2000.",
        "verdict": "TRUE",
        "source": "pib.gov.in",
        "date": "2024-01-01",
        "topic": "agriculture"
    },
    {
        "id": "fact_002",
        "text": "WhatsApp is not banned in India. It continues to operate normally as of 2024.",
        "verdict": "TRUE",
        "source": "meity.gov.in",
        "date": "2024-01-01",
        "topic": "technology"
    },
    {
        "id": "fact_003",
        "text": "Chandrayaan-3 successfully landed on the Moon's south pole on August 23, 2023.",
        "verdict": "TRUE",
        "source": "isro.gov.in",
        "date": "2023-08-23",
        "topic": "space"
    },
    {
        "id": "fact_004",
        "text": "India has 28 states and 8 Union Territories as of 2024.",
        "verdict": "TRUE",
        "source": "india.gov.in",
        "date": "2024-01-01",
        "topic": "geography"
    },
    {
        "id": "fact_005",
        "text": "India's GDP growth rate was 8.2% in FY2023-24 according to the Ministry of Statistics.",
        "verdict": "TRUE",
        "source": "mospi.gov.in",
        "date": "2024-05-31",
        "topic": "economy"
    },
    {
        "id": "fact_006",
        "text": "The RBI repo rate was 6.5% as of mid-2024.",
        "verdict": "TRUE",
        "source": "rbi.org.in",
        "date": "2024-06-01",
        "topic": "economy"
    },
    {
        "id": "fact_007",
        "text": "UPI transactions crossed 10 billion per month in 2023, according to NPCI.",
        "verdict": "TRUE",
        "source": "npci.org.in",
        "date": "2023-12-01",
        "topic": "technology"
    },
    {
        "id": "fact_008",
        "text": "India did not impose a blanket ban on cryptocurrency. Crypto gains are taxed at 30% under Indian law.",
        "verdict": "TRUE",
        "source": "incometax.gov.in",
        "date": "2024-01-01",
        "topic": "finance"
    },
    {
        "id": "fact_009",
        "text": "Aadhaar card is not mandatory for buying a SIM card in India. Multiple ID proofs are accepted.",
        "verdict": "TRUE",
        "source": "trai.gov.in",
        "date": "2024-01-01",
        "topic": "policy"
    },
    {
        "id": "fact_010",
        "text": "India's population crossed 1.4 billion in 2023, making it the most populous country in the world.",
        "verdict": "TRUE",
        "source": "censusindia.gov.in",
        "date": "2023-04-01",
        "topic": "demographics"
    },
]


def load_facts():
    """Load all verified facts into ChromaDB. Skips already-loaded ones."""
    existing = collection.get()["ids"]

    new_facts = [f for f in VERIFIED_FACTS if f["id"] not in existing]

    if not new_facts:
        print(f"✅ Facts DB already loaded ({len(VERIFIED_FACTS)} facts)")
        return

    collection.add(
        ids=[f["id"] for f in new_facts],
        documents=[f["text"] for f in new_facts],
        metadatas=[{
            "verdict": f["verdict"],
            "source": f["source"],
            "date": f["date"],
            "topic": f["topic"]
        } for f in new_facts]
    )
    print(f"✅ Loaded {len(new_facts)} new facts into ChromaDB")


def search_facts(claim, top_k=3):
    """
    Find the most relevant verified facts for a given claim.
    Returns top_k results sorted by similarity.
    """
    results = collection.query(
        query_texts=[claim],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    facts = []
    for i in range(len(results["ids"][0])):
        similarity = 1 - results["distances"][0][i]  # cosine: 1=identical, 0=unrelated
        facts.append({
            "text": results["documents"][0][i],
            "verdict": results["metadatas"][0][i]["verdict"],
            "source": results["metadatas"][0][i]["source"],
            "date": results["metadatas"][0][i]["date"],
            "similarity": round(similarity, 3)
        })

    return facts


# ── Test it directly ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    load_facts()

    test_claims = [
        "PM KISAN gives Rs 10,000 per year to farmers",
        "WhatsApp has been banned in India",
        "Chandrayaan-3 never landed on the moon",
        "India has 29 states",
    ]

    for claim in test_claims:
        print(f"\n🔍 Claim: {claim}")
        results = search_facts(claim, top_k=2)
        for r in results:
            print(f"   📄 [{r['similarity']:.2f}] {r['text'][:70]}...")
            print(f"        Source: {r['source']} | Verdict: {r['verdict']}")