import json
import re
import requests
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen"  # standard qwen model in ollama

# Fallback Category Mapping
ISSUE_CATEGORIES = {
    "ac": "HVAC", "air conditioning": "HVAC", "heating": "HVAC", "hvac": "HVAC",
    "wifi": "IT", "wi-fi": "IT", "internet": "IT", "projector": "IT", "screen": "IT", "hdmi": "IT", "monitor": "IT",
    "water": "Plumbing", "leak": "Plumbing", "toilet": "Plumbing", "faucet": "Plumbing", "pipe": "Plumbing", "sink": "Plumbing",
    "chair": "Furniture", "desk": "Furniture", "table": "Furniture", "bench": "Furniture", "lectern": "Furniture", "blackboard": "Furniture",
    "clean": "Cleanliness", "spill": "Cleanliness", "trash": "Cleanliness", "garbage": "Cleanliness", "dust": "Cleanliness",
    "light": "Electrical", "bulb": "Electrical", "switch": "Electrical", "fan": "Electrical", "power": "Electrical", "electricity": "Electrical", "wire": "Electrical"
}

def analyze_query_fallback(query):
    """
    Analyzes campus queries using regular expressions and keyword matching.
    Returns: (intent, parameters_dict)
    """
    query_lower = query.lower()
    
    # 1. MAINTENANCE_REPORT Intent
    # Keywords indicating a broken item
    broken_keywords = ["broken", "broken", "leak", "leaking", "not working", "malfunction", "damaged", "repair", "fix", "flicker", "flickering", "stuck", "torn"]
    has_broken_kw = any(kw in query_lower for kw in broken_keywords)
    
    # Extract locations (like B204, A102, Library, Canteen, Block A)
    location_match = re.search(r'\b([a-c]\d{3})\b', query_lower)  # matches A101, B204, etc.
    location = None
    if location_match:
        location = location_match.group(1).upper()
    else:
        # Check for named locations
        named_locations = ["library", "canteen", "seminar hall", "sports ground", "parking", "medical center", "main gate", "block a", "block b", "block c"]
        for loc in named_locations:
            if loc in query_lower:
                location = loc.title()
                break

    if has_broken_kw and location:
        # Determine issue type and category
        category = "Other"
        priority = "LOW"
        issue_type = "Maintenance Issue"

        for kw, cat in ISSUE_CATEGORIES.items():
            if kw in query_lower:
                category = cat
                break
        
        # Priority mapping
        high_priority_kws = ["leak", "water leaking", "flooding", "power out", "electricity cut", "compressor failure", "broken ac", "ac broken"]
        medium_priority_kws = ["wi-fi", "wifi", "internet", "projector", "screen", "flicker"]
        
        if any(hp in query_lower for hp in high_priority_kws):
            priority = "HIGH"
        elif any(mp in query_lower for mp in medium_priority_kws):
            priority = "MEDIUM"

        return "MAINTENANCE_REPORT", {
            "location": location,
            "issue_type": category + " Problem",
            "description": query,
            "priority": priority,
            "category": category
        }

    # 2. CLASSROOM_SEARCH Intent
    classroom_keywords = ["classroom", "classrooms", "room", "rooms", "find a room", "study space", "lecture hall"]
    has_room_kw = any(kw in query_lower for kw in classroom_keywords)
    
    # Check for projector / AC requirement
    projector_required = 1 if "projector" in query_lower or "screen" in query_lower else 0
    ac_required = 1 if "ac" in query_lower or "air condition" in query_lower else 0
    
    # Extract capacity
    capacity = 0
    capacity_match = re.search(r'(\d+)\s*(students|people|seats|capacity)?', query_lower)
    if capacity_match:
        # Ignore years or room numbers
        val = int(capacity_match.group(1))
        if val < 500 and not (val >= 100 and val <= 299): # standard capacity, avoid matching room number range
            capacity = val

    if has_room_kw or capacity > 0 or projector_required or ac_required:
        return "CLASSROOM_SEARCH", {
            "capacity": capacity if capacity > 0 else 0,
            "projector": projector_required,
            "ac": ac_required
        }

    # 3. LOCATION_SEARCH Intent
    location_keywords = ["where is", "how do i get to", "direction", "directions", "location of", "map of", "find the", "way to"]
    has_loc_kw = any(kw in query_lower for kw in location_keywords)
    
    named_locations = ["library", "canteen", "seminar hall", "sports ground", "parking", "medical center", "main gate", "block a", "block b", "block c"]
    target_location = None
    for loc in named_locations:
        if loc in query_lower:
            target_location = loc.title()
            break

    if target_location and (has_loc_kw or any(kw in query_lower for kw in ["library", "canteen", "sports ground", "seminar hall"])):
        return "LOCATION_SEARCH", {
            "location": target_location
        }

    # 4. EVENT_SEARCH Intent
    event_keywords = ["event", "events", "workshop", "meetup", "match", "club", "happening", "today", "calendar"]
    if any(kw in query_lower for kw in event_keywords) and "today" in query_lower:
        return "EVENT_SEARCH", {}

    # 5. OCCUPANCY_QUERY Intent
    occupancy_keywords = ["occupancy", "occupancies", "crowded", "how busy", "crowd", "people at"]
    if any(kw in query_lower for kw in occupancy_keywords):
        target_building = None
        for bld in ["block a", "block b", "block c", "library", "canteen"]:
            if bld in query_lower:
                target_building = bld.title()
                break
        return "OCCUPANCY_QUERY", {
            "building": target_building
        }

    # 6. GENERAL_CAMPUS_QUERY Fallback
    return "GENERAL_CAMPUS_QUERY", {}


def analyze_query_ai(query):
    """
    Queries Ollama/Qwen model. If unavailable, calls the fallback analyser.
    Returns: (intent, parameters_dict)
    """
    system_prompt = """
    You are CampusIQ, the AI smart campus assistant. Analyze the user's query and output a valid JSON object ONLY.
    Intents MUST be one of:
    - CLASSROOM_SEARCH: For finding study rooms, lecture halls, or general classroom availability.
    - LOCATION_SEARCH: For asking where buildings/facilities are on the map.
    - EVENT_SEARCH: For asking about events, seminars, matches today.
    - MAINTENANCE_REPORT: For reporting broken equipment like AC, projectors, lights, leaks, etc.
    - OCCUPANCY_QUERY: For asking about crowd levels, building occupancies.
    - GENERAL_CAMPUS_QUERY: For general greetings or topics not covered.

    For each intent, parse parameters:
    1. CLASSROOM_SEARCH: {"capacity": integer (or 0 if not specified), "projector": 1 or 0, "ac": 1 or 0}
    2. LOCATION_SEARCH: {"location": "Library" / "Canteen" / "Seminar Hall" / "Sports Ground" / "Main Gate" / "Block A" / "Block B" / "Block C" / "Parking" / "Medical Center" or null}
    3. EVENT_SEARCH: {}
    4. MAINTENANCE_REPORT: {"location": room/facility name like "B204" or "Library", "issue_type": "AC problem"/"Furniture"/"Plumbing", "description": full description, "priority": "LOW"/"MEDIUM"/"HIGH", "category": "HVAC"/"Electrical"/"IT"/"Furniture"/"Plumbing"/"Cleanliness"/"Other"}
    5. OCCUPANCY_QUERY: {"building": "Block A"/"Library" etc. or null}
    6. GENERAL_CAMPUS_QUERY: {}

    Example Output format:
    {
      "intent": "CLASSROOM_SEARCH",
      "parameters": {"capacity": 40, "projector": 1, "ac": 1}
    }
    Never output text outside the JSON block. Do not use code blocks (e.g. ```json). Just the raw json object.
    """
    
    payload = {
        "model": MODEL_NAME,
        "prompt": f"System: {system_prompt}\nUser: {query}\nResponse:",
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }
    
    try:
        # Short timeout of 3.0 seconds to prevent locking the UI in a hackathon
        response = requests.post(OLLAMA_URL, json=payload, timeout=3.0)
        if response.status_code == 200:
            res_json = response.json()
            response_text = res_json.get("response", "").strip()
            
            # Extract JSON from response text (if AI added backticks or extra text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                intent = parsed.get("intent", "GENERAL_CAMPUS_QUERY")
                parameters = parsed.get("parameters", {})
                return intent, parameters
    except Exception as e:
        print(f"Ollama/Qwen is unavailable or timed out: {e}. Switching to Keyword Fallback.")
    
    # If anything fails, use the keyword analyzer
    return analyze_query_fallback(query)


def classify_maintenance_issue(description):
    """
    Specialized classification for maintenance reports using Qwen / keyword fallback.
    Returns: (category, priority, summary)
    """
    # Try using Ollama
    system_prompt = """
    You are an automated maintenance ticket triage system. Analyze the maintenance issue.
    Classify into:
    Category: HVAC, IT, Plumbing, Furniture, Cleanliness, Electrical, Other
    Priority: LOW, MEDIUM, HIGH (HIGH: water leaks, AC broken in hot rooms, power outages; MEDIUM: projector issues, flickering lights, wifi down; LOW: broken chairs, overflow trash, humming fan).
    Provide a concise 1-sentence summary.
    
    Output ONLY a valid JSON:
    {"category": "HVAC", "priority": "HIGH", "summary": "Concise summary"}
    Do not output markdown code blocks.
    """
    
    payload = {
        "model": MODEL_NAME,
        "prompt": f"System: {system_prompt}\nIssue description: {description}\nResponse:",
        "stream": False,
        "options": {"temperature": 0.1}
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=3.0)
        if response.status_code == 200:
            res_json = response.json()
            response_text = res_json.get("response", "").strip()
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                return (
                    parsed.get("category", "Other"),
                    parsed.get("priority", "LOW"),
                    parsed.get("summary", "Reported maintenance issue")
                )
    except Exception:
        pass
    
    # Fallback keyword classifier
    query_lower = description.lower()
    category = "Other"
    priority = "LOW"
    
    for kw, cat in ISSUE_CATEGORIES.items():
        if kw in query_lower:
            category = cat
            break
            
    high_priority_kws = ["leak", "water leaking", "flooding", "power out", "electricity cut", "compressor failure", "broken ac", "ac broken"]
    medium_priority_kws = ["wi-fi", "wifi", "internet", "projector", "screen", "flicker"]
    
    if any(hp in query_lower for hp in high_priority_kws):
        priority = "HIGH"
    elif any(mp in query_lower for mp in medium_priority_kws):
        priority = "MEDIUM"
        
    summary = f"Reported {category.lower()} issue: {description[:50]}..."
    return category, priority, summary
