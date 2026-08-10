from pipeline.ingest  import fetch_schemes
from pipeline.vectordb import store

print("Stage 1: Fetching schemes...")
fetch_schemes()

print("Stage 2+3: Embedding and storing...")
store()

print("Done! ChromaDB is ready.")