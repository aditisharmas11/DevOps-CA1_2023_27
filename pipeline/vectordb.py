import chromadb
from config import CHROMA_PATH, COLLECTION
from pipeline.embed import chunk_and_embed

def store():
    client     = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(COLLECTION)

    chunks = chunk_and_embed()

    collection.add(
        ids        = [c["id"]        for c in chunks],
        documents  = [c["text"]      for c in chunks],
        embeddings = [c["embedding"] for c in chunks],
        metadatas  = [c["metadata"]  for c in chunks],
    )
    print(f"Stored {len(chunks)} chunks in ChromaDB")

if __name__ == "__main__":
    store()