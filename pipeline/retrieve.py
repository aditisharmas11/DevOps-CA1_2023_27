import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_PATH, COLLECTION, EMBED_MODEL, TOP_K

client     = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(COLLECTION)
model      = SentenceTransformer(EMBED_MODEL)

def build_filter(profile: dict):
    if profile.get("state") and profile["state"] != "central":
        return {"state": {"$in": [profile["state"], "central"]}}
    return None

def retrieve(query: str, profile: dict):
    embedding = model.encode(query).tolist()
    where     = build_filter(profile)

    print(f"[Retrieve] Filter applied: {where}")

    results = collection.query(
        query_embeddings = [embedding],
        n_results        = TOP_K,
        where            = where,
        include          = ["documents", "metadatas", "distances"]
    )

    docs  = results["documents"][0]
    metas = results["metadatas"][0]

    print(f"[Retrieve] Got {len(docs)} chunks")
    if metas:
        print(f"[Retrieve] Sample metadata: {metas[0]}")

    return [{"text": d, "meta": m} for d, m in zip(docs, metas)]