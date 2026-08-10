# PolicyPal
#PolicyPal — India's AI-Powered Government Scheme Navigator

> Team Name: Prompt404  
> Team Members:Riya Agrawal · Saumya Kumar · Reuel Menon

---

## 📌 The Problem

Millions of Indians miss government schemes they already qualify for. Here's why:

- **Information Overload** — 1,000+ central & state schemes spread across portals, impossible to manually track
- **Poor Discoverability** — Schemes buried in PDFs, Hindi/English mix, no unified search
- **Complex Eligibility** — Income, caste, occupation, region, age — multi-dimensional criteria that's hard to self-assess
- **Last-Mile Failure** — People don't apply simply because they don't know they qualify — money left unused

---

## 💡 The Solution

**PolicyPal** is an AI-powered scheme navigator that takes a citizen's profile (income, occupation, state, caste category) and instantly matches them to every government scheme they qualify for — with benefit amounts, eligibility reasons, and direct apply links.

### How it works

A user inputs their profile → PolicyPal builds an eligibility filter → retrieves matching scheme chunks from a vector database → passes them to an LLM → returns a ranked, actionable list of schemes in Hindi or English.

---

## ✨ Key Innovations

- **Eligibility-Aware Retrieval** — Metadata filters (income, state, occupation, category) are applied *before* vector search — dramatically improving precision over naive RAG. Only relevant scheme chunks reach the LLM.
- **Multilingual Support** — Handles Hindi + English queries natively using a multilingual embedding model.
- **Structured Scheme Metadata** — Each scheme chunk is enriched with structured fields (`income_limit`, `category`, `occupation`) enabling SQL-like filtering inside vector search.
- **Local LLM via Ollama** — Runs entirely offline using Llama 3.2, no API costs, no internet dependency during demo.

---

## 🏗️ RAG Pipeline

```
Data Sources → Chunking & Embeddings → Vector DB → Retrieval & Ranking → LLM Response
    (1)                 (2)                (3)              (4)                (5)
```

| Stage | What happens |
|-------|-------------|
| 1. Data Sources | Schemes loaded from `schemes.json` (sourced from MyScheme.gov.in) |
| 2. Chunking & Embeddings | Text split into chunks, metadata extracted, embedded with `paraphrase-multilingual-mpnet-base-v2` |
| 3. Vector DB | Chunks + embeddings stored in ChromaDB with metadata index |
| 4. Retrieval & Ranking | Eligibility pre-filter built from user profile → semantic search → top-K results |
| 5. LLM Response | Llama 3.2 (via Ollama) generates structured scheme recommendations |

---

## 📁 Project Structure

```
PolicyPal/
├── chroma_db/              # Persisted vector database (auto-generated)
├── data/                   # Raw and processed scheme data
├── pipeline/
│   ├── schemes.json        # Source scheme data
│   ├── ingest.py           # Stage 1: Load + clean + extract metadata from schemes
│   ├── embed.py            # Stage 2: Chunk text + generate embeddings
│   ├── vectordb.py         # Stage 3: Store chunks in ChromaDB
│   ├── retrieve.py         # Stage 4: Eligibility filter + semantic search
│   └── llm.py              # Stage 5: Ollama Llama 3.2 response generation
├── app.py                  # Streamlit UI — full demo interface
├── config.py               # Model names, DB path, settings
├── run_pipeline.py         # One-shot script: runs stages 1→2→3
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Embeddings | `paraphrase-multilingual-mpnet-base-v2` (sentence-transformers) |
| Vector DB | ChromaDB (persistent, local) |
| LLM | Llama 3.2 via Ollama (fully local, no API key) |
| Chunking | LangChain RecursiveCharacterTextSplitter |
| Frontend | Streamlit |
| Language | Python 3.10+ |

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed on your machine

### 1. Clone the repository

```bash
git clone https://github.com/your-username/policypal.git
cd policypal
```

### 2. Install Python dependencies

```bash
pip install streamlit chromadb sentence-transformers langchain requests python-dotenv
```

### 3. Install and start Ollama

```bash
# Download from https://ollama.com and install, then:
ollama pull llama3.2
ollama serve
# Ollama will run on http://localhost:11434
```

### 4. Run the ingestion pipeline (do this ONCE)

This fetches schemes, chunks them, embeds them, and stores everything in ChromaDB.

```bash
python run_pipeline.py
```

Expected output:
```
Stage 1: Loading schemes...
Loaded 120 schemes from schemes.json
Stage 2+3: Embedding and storing in ChromaDB...
Created 340 chunks
Stored 340 chunks in ChromaDB
Done! ChromaDB is ready.
```

### 5. Launch the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 🚀 How to Use

1. Fill in your profile in the sidebar:
   - **Annual Income** (₹)
   - **Occupation** (Student / Farmer / Worker / General)
   - **Caste Category** (General / SC / ST / OBC)
   - **Other** (Women / Disabled / Minority — optional)

2. Type your query in the chat box, e.g.:
   - *"What schemes am I eligible for?"*
   - *"Are there any scholarships for me?"*

3. PolicyPal returns a ranked list of matching schemes with benefit amounts and apply instructions.

---

## 🧪 Test the Pipeline (without UI)

```bash
# Quick retrieval test in Python shell
python -c "
from pipeline.retrieve import retrieve
results = retrieve('scholarships for students', {
    'income': 100000,
    'occupation': 'student',
    'category': 'obc',
    'other': ''
})
for r in results:
    print(r['meta']['title'])
"
```

---

## 📊 Dataset

Schemes are sourced from **MyScheme.gov.in** — India's official government scheme portal. The `schemes.json` file contains scheme records with the following fields:

- `Scheme Name`
- `Description`
- `Eligibility`
- `Benefits`
- `Required Documents`

Metadata (income limit, occupation, category) is automatically extracted from the eligibility text using keyword parsing in `ingest.py`.

---

## 🔧 Configuration

Edit `config.py` to change models or paths:

```python
OLLAMA_URL   = "http://localhost:11434/api/generate"
MODEL        = "llama3.2"
EMBED_MODEL  = "paraphrase-multilingual-mpnet-base-v2"
CHROMA_PATH  = "./chroma_db"
COLLECTION   = "schemes"
TOP_K        = 5
```

---

## 📈 Impact

| Metric | Value |
|--------|-------|
| Eligible Citizens | 80 Crore+ |
| Annual Scheme Budget | ₹20L Crore |
| Schemes Underutilized | ~40% |

Even 1% adoption = **80 lakh people** discovering schemes they qualify for.

---
