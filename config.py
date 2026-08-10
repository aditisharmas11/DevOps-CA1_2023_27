import os
from dotenv import load_dotenv
load_dotenv()

OLLAMA_URL  = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL       = os.getenv("OLLAMA_MODEL", "llama3.2")

EMBED_MODEL = "paraphrase-multilingual-mpnet-base-v2"
CHROMA_PATH = "./chroma_db"
COLLECTION  = "schemes"
TOP_K       = 5