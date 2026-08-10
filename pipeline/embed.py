import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

def chunk_and_embed():
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

    print("Loading embedding model (downloads ~400MB on first run, please wait)...")
    model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
    print("Model loaded\n")

    with open("data/raw_schemes.json", encoding="utf-8") as f:
        schemes = json.load(f)

    all_chunks = []
    for s in schemes:
        text = f"{s['title']}\n{s['description']}\n{s['eligibility']}\n{s['benefits']}"
        chunks = splitter.split_text(text)

        for i, chunk in enumerate(chunks):
            embedding = model.encode(chunk).tolist()
            all_chunks.append({
                "id":        f"{s['id']}_chunk{i}",
                "text":      chunk,
                "embedding": embedding,
                "metadata": {
                    "scheme_id":    str(s["id"]),
                    "title":        s["title"],
                    "state":        s["state"],
                    "income_limit": int(s["income_limit"]),
                    "apply_url":    s["apply_url"],
                    "ministry":     s["ministry"],
                }
            })
        print(f"  {s['title']}")

    print(f"\n Done — {len(all_chunks)} chunks from {len(schemes)} schemes")
    return all_chunks


if __name__ == "__main__":
    chunks = chunk_and_embed()

    print("\n--- Sample output (first chunk) ---")
    print("ID:       ", chunks[0]["id"])
    print("Text:     ", chunks[0]["text"][:100], "...")
    print("Embedding:", str(chunks[0]["embedding"][:5]), "...")
    print("Metadata: ", chunks[0]["metadata"])