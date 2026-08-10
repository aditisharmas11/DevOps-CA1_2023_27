import json
import os

def fetch_schemes():
    input_path = "schemes.json"

    with open(input_path, encoding="utf-8") as f:
        raw = json.load(f)

    cleaned = []
    for i, s in enumerate(raw):
        eligibility_text = s.get("Eligibility", "")
        if isinstance(eligibility_text, list):
            eligibility_text = " ".join(eligibility_text)
        elif isinstance(eligibility_text, dict):
            eligibility_text = " ".join(str(v) for v in eligibility_text.values())
        elif not isinstance(eligibility_text, str):
            eligibility_text = str(eligibility_text)
        
        # parse income limit
        income_limit = 999999
        if "1,00,000" in eligibility_text or "1 lakh" in eligibility_text.lower():
            income_limit = 100000
        elif "2 lakh" in eligibility_text.lower() or "2,00,000" in eligibility_text:
            income_limit = 200000
        elif "8 lakh" in eligibility_text.lower() or "8,00,000" in eligibility_text:
            income_limit = 800000

        # detect occupation
        occupation = []
        text_lower = eligibility_text.lower()
        if "student" in text_lower:
            occupation.append("student")
        if "farmer" in text_lower or "agriculture" in text_lower:
            occupation.append("farmer")
        if not occupation:
            occupation.append("general")

        other = []
        if "woman" in text_lower or "girl" in text_lower or "female" in text_lower:
            other.append("women")
        if "disabled" in text_lower or "disability" in text_lower or "abled" in text_lower:
            other.append("disabled")


        # detect category
        category = ["general"]
        if "sc" in text_lower or "scheduled caste" in text_lower or "adi dravidar" in text_lower:
            category.append("sc")
        if "st" in text_lower or "tribal" in text_lower:
            category.append("st")
        if "obc" in text_lower or "backward" in text_lower:
            category.append("obc")
        if "minority" in text_lower or "muslim" in text_lower or "christian" in text_lower:
            category.append("minority")

        cleaned.append({
            "id":           f"scheme_{i}",
            "title":        s.get("Scheme Name", "Unknown"),
            "description":  s.get("Description", ""),
            "eligibility":  s.get("Eligibility", ""),
            "benefits":     s.get("Benefits", ""),
            "documents":    s.get("Required Documents", ""),
            "state":        "central",
            "ministry":     "",
            "apply_url":    "https://myscheme.gov.in",
            "income_limit": income_limit,
           "occupation":   ",".join(occupation),  
            "other":        ",".join(other),     
            "category":     ",".join(category)
        })

    os.makedirs("data", exist_ok=True)
    with open("data/raw_schemes.json", "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f" Loaded {len(cleaned)} schemes from schemes.json")
    print(f"   Sample: {cleaned[0]['title']}")
    return cleaned


if __name__ == "__main__":
    fetch_schemes()

