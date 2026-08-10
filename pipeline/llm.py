
import requests
from config import OLLAMA_URL, MODEL

SYSTEM = """You are PolicyPal, an AI that helps Indian citizens find government 
schemes they qualify for. Reply in the same language the user writes in.
Always respond with a numbered list of schemes. For each scheme include:
- Scheme name
- What benefit they get
- One line on why they qualify
- How to apply (one sentence)"""

def generate(query: str, retrieved: list, profile: dict) -> str:
    context = "\n\n".join([
        f"Scheme: {r['meta']['title']}\n{r['text']}\nApply at: {r['meta']['apply_url']}"
        for r in retrieved
    ])

    prompt = f"""User profile: {profile}

Relevant schemes from database:
{context}

User asked: {query}

List the schemes this user qualifies for."""

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model":  MODEL,
            "stream": False,
            "messages": [
                {"role": "system",  "content": SYSTEM},
                {"role": "user",    "content": prompt},
            ]
        },
        timeout=180
    )
    response.raise_for_status()
    return response.json()["message"]["content"]
