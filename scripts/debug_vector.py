import json
from hybrid_search.index.vector import VectorIndex
"""
Debug script for validating vector search behavior.

Usage:
    python3 -m scripts.debug_vector
"""

# Load documents
docs = []
with open("data/processed/docs.jsonl") as f:
    for line in f:
        docs.append(json.loads(line))

print(f"Loaded {len(docs)} documents")

# Build index
index = VectorIndex().fit(docs)

print("Vector index built successfully")

# Test queries
queries = [
    "Sri Lankan actress",
    "beauty pageant winner",
    "university degree",
    "person working in films",
]

for q in queries:
    print("\n" + "=" * 50)
    print("QUERY:", q)

    results = index.search(q, top_k=3)

    for r in results:
        print(f"{r.score:.4f} | {r.title}")