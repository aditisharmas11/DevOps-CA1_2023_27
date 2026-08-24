import os
import sqlite3
import random
from datetime import datetime, date
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import DB_PATH, get_db_connection
import ai

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes to connect with the Vite frontend

# Helper to format rows as dictionaries
def query_db(query, args=(), one=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, args)
    rv = cursor.fetchall()
    conn.commit() # Commit in case of updates
    conn.close()
    
    # Format rows as dict
    result = [dict(ix) for ix in rv]
    return (result[0] if result else None) if one else result

# Helper to execute modifications
def execute_db(query, args=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

# ----------------- AUTHENTICATION -----------------
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    user = query_db("SELECT * FROM users WHERE email = ? AND password = ?", (email, password), one=True)
    if user:
        return jsonify({
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "role": user['role']
        })
    else:
        return jsonify({"error": "Invalid email or password"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role', 'student')
    
    if not email or not password or not name:
        return jsonify({"error": "Email, password and name are required"}), 400
        
    try:
        user_id = execute_db(
            "INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)",
            (email, password, name, role)
        )
        return jsonify({
            "id": user_id,
            "email": email,
            "name": name,
            "role": role
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400

# ----------------- CLASSROOMS -----------------
@app.route('/api/classrooms', methods=['GET'])
def get_classrooms():
    building = request.args.get('building')
    min_capacity = request.args.get('capacity', type=int)
    available_only = request.args.get('available') # True/False
    has_projector = request.args.get('projector') # 1/0
    
    query = "SELECT * FROM classrooms WHERE 1=1"
    params = []
    
    if building:
        query += " AND building = ?"
        params.append(building)
    if min_capacity:
        query += " AND capacity >= ?"
        params.append(min_capacity)
    if available_only == 'true':
        query += " AND status = 'AVAILABLE'"
    if has_projector == '1':
        query += " AND projector = 1"
        
    query += " ORDER BY name ASC"
    classrooms = query_db(query, params)
    return jsonify(classrooms)

@app.route('/api/classrooms/<int:classroom_id>', methods=['GET'])
def get_classroom(classroom_id):
    classroom = query_db("SELECT * FROM classrooms WHERE id = ?", (classroom_id,), one=True)
    if classroom:
        return jsonify(classroom)
    return jsonify({"error": "Classroom not found"}), 404

# ----------------- LOCATIONS -----------------
@app.route('/api/locations', methods=['GET'])
def get_locations():
    locations = query_db("SELECT * FROM locations ORDER BY name ASC")
    return jsonify(locations)

# ----------------- EVENTS -----------------
@app.route('/api/events', methods=['GET'])
def get_events():
    # Fetch events
    events = query_db("SELECT * FROM events ORDER BY date ASC, time ASC")
    return jsonify(events)

# ----------------- MAINTENANCE -----------------
@app.route('/api/maintenance', methods=['GET'])
def get_maintenance():
    tickets = query_db("SELECT * FROM maintenance ORDER BY id DESC")
    return jsonify(tickets)

@app.route('/api/maintenance', methods=['POST'])
def create_maintenance():
    data = request.get_json() or {}
    issue_type = data.get('issue_type')
    location = data.get('location')
    description = data.get('description')
    
    if not issue_type or not location or not description:
        return jsonify({"error": "Issue type, location and description are required"}), 400
        
    # Auto-classify Category & Priority using AI / Fallback
    category, priority, summary = ai.classify_maintenance_issue(description)
    
    # Generate unique ticket number CIQ-XXXX
    # Find next ticket id
    res = query_db("SELECT MAX(id) as max_id FROM maintenance", one=True)
    next_id = 1001
    if res and res['max_id']:
        next_id = 1001 + res['max_id']
        
    ticket_no = f"CIQ-{next_id}"
    created_at = date.today().isoformat()
    status = "OPEN"
    
    execute_db(
        "INSERT INTO maintenance (ticket_no, issue_type, location, description, priority, status, created_at, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (ticket_no, issue_type, location, description, priority, status, created_at, category)
    )
    
    new_ticket = query_db("SELECT * FROM maintenance WHERE ticket_no = ?", (ticket_no,), one=True)
    return jsonify(new_ticket), 201

@app.route('/api/maintenance/<int:ticket_id>', methods=['PUT'])
def update_maintenance(ticket_id):
    data = request.get_json() or {}
    status = data.get('status')
    
    if not status or status not in ['OPEN', 'IN PROGRESS', 'RESOLVED']:
        return jsonify({"error": "Invalid ticket status"}), 400
        
    execute_db("UPDATE maintenance SET status = ? WHERE id = ?", (status, ticket_id))
    updated_ticket = query_db("SELECT * FROM maintenance WHERE id = ?", (ticket_id,), one=True)
    if updated_ticket:
        return jsonify(updated_ticket)
    return jsonify({"error": "Ticket not found"}), 404

# ----------------- OCCUPANCY -----------------
@app.route('/api/occupancy', methods=['GET'])
def get_occupancy():
    occupancy_list = query_db("SELECT * FROM occupancy ORDER BY building_name ASC")
    return jsonify(occupancy_list)

@app.route('/api/occupancy/simulate', methods=['POST'])
def simulate_occupancy():
    # Update building occupancy levels randomly to simulate dynamic IoT updates
    buildings = ["Block A", "Block B", "Block C", "Library", "Canteen"]
    for b in buildings:
        new_pct = random.randint(20, 95)
        execute_db(
            "UPDATE occupancy SET occupancy_pct = ?, updated_at = ? WHERE building_name = ?",
            (new_pct, datetime.now().isoformat(), b)
        )
        # Update locations table as well to sync Leaflet map data
        execute_db(
            "UPDATE locations SET occupancy_pct = ? WHERE name = ?",
            (new_pct, b)
        )
        
    # Also randomly update classroom occupancy and status
    classrooms = query_db("SELECT * FROM classrooms")
    for r in classrooms:
        # Don't change MAINTENANCE rooms status
        if r['status'] == 'MAINTENANCE':
            continue
            
        new_occ = random.randint(0, 100)
        
        # Decide status based on occupancy
        if new_occ == 0:
            status = 'AVAILABLE'
        elif new_occ >= 90:
            status = 'FULL'
        elif new_occ >= 50:
            status = 'OCCUPIED'
        else:
            status = 'AVAILABLE'
            
        execute_db(
            "UPDATE classrooms SET occupancy_pct = ?, status = ? WHERE id = ?",
            (new_occ, status, r['id'])
        )
        
    updated_occupancy = query_db("SELECT * FROM occupancy ORDER BY building_name ASC")
    return jsonify({
        "message": "Occupancy data successfully simulated.",
        "occupancy": updated_occupancy
    })

# ----------------- SENSORS -----------------
# Simulated sensors data list
SIMULATED_SENSORS = [
    {"id": "s1", "name": "B204 Occupancy Sensor", "type": "Occupancy", "value": "12 students", "status": "ONLINE", "last_updated": "Just now"},
    {"id": "s2", "name": "B204 Temperature Sensor", "type": "Temperature", "value": "22.4 °C", "status": "ONLINE", "last_updated": "Just now"},
    {"id": "s3", "name": "Block B Energy Sensor", "type": "Energy", "value": "42.1 kW", "status": "ONLINE", "last_updated": "Just now"},
    {"id": "s4", "name": "Library Noise Sensor", "type": "Noise Level", "value": "35 dB (Quiet)", "status": "ONLINE", "last_updated": "Just now"},
    {"id": "s5", "name": "Main Gate Flow Counter", "type": "Inflow/Outflow", "value": "148 entry/hr", "status": "ONLINE", "last_updated": "Just now"}
]

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    return jsonify(SIMULATED_SENSORS)

@app.route('/api/sensors/simulate', methods=['POST'])
def simulate_sensors():
    # Perturb sensor values slightly
    SIMULATED_SENSORS[0]["value"] = f"{random.randint(5, 55)} students"
    SIMULATED_SENSORS[1]["value"] = f"{round(random.uniform(20.5, 25.8), 1)} °C"
    SIMULATED_SENSORS[2]["value"] = f"{round(random.uniform(35.0, 50.0), 1)} kW"
    SIMULATED_SENSORS[3]["value"] = f"{random.randint(30, 65)} dB"
    if int(SIMULATED_SENSORS[3]["value"].split()[0]) > 55:
        SIMULATED_SENSORS[3]["value"] += " (Moderate)"
    else:
        SIMULATED_SENSORS[3]["value"] += " (Quiet)"
    SIMULATED_SENSORS[4]["value"] = f"{random.randint(80, 220)} entry/hr"
    
    for s in SIMULATED_SENSORS:
        # Occasionally simulate a sensor going offline
        s["status"] = "ONLINE" if random.random() > 0.05 else "OFFLINE"
        s["last_updated"] = "Just now" if s["status"] == "ONLINE" else "5 mins ago"
        
    return jsonify({
        "message": "Sensor telemetry simulated.",
        "sensors": SIMULATED_SENSORS
    })

# ----------------- CO-PILOT AI ENGINE -----------------
@app.route('/api/copilot', methods=['POST'])
def copilot():
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({"message": "Please enter a valid query.", "intent": "GENERAL_CAMPUS_QUERY", "action": None})
        
    # Run Qwen Classifier / Fallback
    intent, params = ai.analyze_query_ai(query)
    
    response_msg = ""
    action = None
    
    if intent == "CLASSROOM_SEARCH":
        req_capacity = params.get("capacity", 0)
        req_proj = params.get("projector", 0)
        req_ac = params.get("ac", 0)
        
        # SQL Query classrooms
        sql = "SELECT * FROM classrooms WHERE status = 'AVAILABLE'"
        args = []
        if req_capacity > 0:
            sql += " AND capacity >= ?"
            args.append(req_capacity)
        if req_proj:
            sql += " AND projector = 1"
        if req_ac:
            sql += " AND ac = 1"
            
        sql += " ORDER BY capacity ASC LIMIT 3"
        rooms = query_db(sql, args)
        
        if rooms:
            best_room = rooms[0]
            # Format response
            response_msg = f"Based on your requirements (Capacity: {req_capacity if req_capacity > 0 else 'Any'}, Projector: {'Required' if req_proj else 'Any'}, AC: {'Required' if req_ac else 'Any'}), the best match is **{best_room['name']}**.\n\n"
            response_msg += f"- **Room Name:** {best_room['name']} ({best_room['building']})\n"
            response_msg += f"- **Capacity:** {best_room['capacity']} seats\n"
            response_msg += f"- **Occupancy:** {best_room['occupancy_pct']}%\n"
            response_msg += f"- **Projector:** {'✓ Available' if best_room['projector'] == 1 else '✗ None'}\n"
            response_msg += f"- **AC Status:** {'✓ Working' if best_room['ac'] == 1 else '✗ Not Working/None'}\n"
            response_msg += f"- **Current Status:** AVAILABLE"
            
            # Action object
            action = {
                "type": "viewMap",
                "target": best_room['building'],
                "room": best_room['name'],
                "details": best_room
            }
        else:
            # Try relaxing criteria (ignore projector/ac first, check for available rooms)
            relaxed_sql = "SELECT * FROM classrooms WHERE status = 'AVAILABLE'"
            relaxed_args = []
            if req_capacity > 0:
                relaxed_sql += " AND capacity >= ?"
                relaxed_args.append(req_capacity)
            relaxed_sql += " ORDER BY capacity ASC LIMIT 1"
            relaxed_rooms = query_db(relaxed_sql, relaxed_args)
            
            if relaxed_rooms:
                best_room = relaxed_rooms[0]
                response_msg = f"I couldn't find a room that perfectly matches all your criteria (capacity, projector, and AC). However, I recommend **{best_room['name']}** as a close alternative:\n\n"
                response_msg += f"- **Room:** {best_room['name']} ({best_room['building']})\n"
                response_msg += f"- **Capacity:** {best_room['capacity']} seats\n"
                response_msg += f"- **Projector:** {'✓ Available' if best_room['projector'] == 1 else '✗ None'}\n"
                response_msg += f"- **AC:** {'✓ Working' if best_room['ac'] == 1 else '✗ Not Working'}\n"
                response_msg += "\nWould you like me to show this room on the map?"
                
                action = {
                    "type": "viewMap",
                    "target": best_room['building'],
                    "room": best_room['name'],
                    "details": best_room
                }
            else:
                response_msg = "I'm sorry, I couldn't find any available classrooms that accommodate your requested capacity. You may check the **Classrooms** page to view occupancy details."
                
    elif intent == "LOCATION_SEARCH":
        loc_name = params.get("location")
        if loc_name:
            location_info = query_db("SELECT * FROM locations WHERE name LIKE ?", (f"%{loc_name}%",), one=True)
            if location_info:
                response_msg = f"Here is the location info for the **{location_info['name']}**:\n\n"
                response_msg += f"- **Open Until:** {location_info['open_until']}\n"
                response_msg += f"- **Current Occupancy:** {location_info['occupancy_pct']}%\n"
                if location_info['study_rooms'] > 0:
                    response_msg += f"- **Study Rooms:** {location_info['study_rooms']} rooms\n"
                response_msg += f"- **Description:** {location_info['details']}\n"
                
                action = {
                    "type": "viewMap",
                    "target": location_info['name']
                }
            else:
                response_msg = f"I know about the campus locations like Block A, Block B, Block C, Library, Canteen, and Seminar Hall. I couldn't find details for '{loc_name}'. Let me open the Campus Map for you."
                action = {"type": "viewMap", "target": "Library"}
        else:
            response_msg = "Which location are you looking for? You can search for Block A, Block B, Block C, Canteen, Library, Canteen, Sports Ground, Seminar Hall, etc."
            action = {"type": "viewMap", "target": "Library"}
            
    elif intent == "EVENT_SEARCH":
        today_str = date.today().isoformat()
        events = query_db("SELECT * FROM events WHERE date = ?", (today_str,))
        
        if events:
            response_msg = "Here are the events happening **today** on campus:\n\n"
            for ev in events:
                response_msg += f"### {ev['title']}\n"
                response_msg += f"- **Time:** {ev['time']}\n"
                response_msg += f"- **Location:** {ev['location']}\n"
                response_msg += f"- **Category:** {ev['category']}\n"
                response_msg += f"- **Description:** {ev['description']}\n\n"
        else:
            response_msg = "There are no events scheduled in the database for today. You can check the complete schedule on the **Events** page."
            
        action = {"type": "viewEvents"}
        
    elif intent == "MAINTENANCE_REPORT":
        loc = params.get("location", "Unknown Location")
        desc = params.get("description", query)
        priority = params.get("priority", "LOW")
        cat = params.get("category", "Other")
        issue_type = params.get("issue_type", f"{cat} malfunction")
        
        # Register the ticket automatically
        res = query_db("SELECT MAX(id) as max_id FROM maintenance", one=True)
        next_id = 1001
        if res and res['max_id']:
            next_id = 1001 + res['max_id']
            
        ticket_no = f"CIQ-{next_id}"
        created_at = date.today().isoformat()
        status = "OPEN"
        
        execute_db(
            "INSERT INTO maintenance (ticket_no, issue_type, location, description, priority, status, created_at, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ticket_no, issue_type, loc, desc, priority, status, created_at, cat)
        )
        
        response_msg = f"I have automatically filed a maintenance ticket for you!\n\n"
        response_msg += f"- **Ticket:** `#{ticket_no}`\n"
        response_msg += f"- **Issue Category:** {cat}\n"
        response_msg += f"- **Location:** {loc}\n"
        response_msg += f"- **Priority:** {priority}\n"
        response_msg += f"- **Status:** OPEN\n\n"
        response_msg += f"Our campus maintenance team has been alerted and will update the ticket as progress is made."
        
        action = {
            "type": "viewMaintenance",
            "ticket": ticket_no
        }
        
    elif intent == "OCCUPANCY_QUERY":
        bld = params.get("building")
        if bld:
            occ_info = query_db("SELECT * FROM occupancy WHERE building_name LIKE ?", (f"%{bld}%",), one=True)
            if occ_info:
                response_msg = f"The occupancy level for **{occ_info['building_name']}** is currently **{occ_info['occupancy_pct']}%**."
            else:
                response_msg = f"I couldn't find building occupancy data for '{bld}'."
        else:
            occupancies = query_db("SELECT * FROM occupancy")
            response_msg = "Here are the current occupancies across campus buildings:\n\n"
            for o in occupancies:
                response_msg += f"- **{o['building_name']}:** {o['occupancy_pct']}%\n"
                
        action = {"type": "viewOccupancy"}
        
    else: # GENERAL_CAMPUS_QUERY
        response_msg = "Hello! I am **CampusIQ**, your AI Smart Campus Copilot. 👋\n\nI can help you with:\n- **Finding rooms:** *'Find me a classroom for 40 students with a projector'* \n- **Navigating the campus:** *'Where is the library?'*\n- **Checking events:** *'What events are happening today?'*\n- **Reporting maintenance:** *'The AC in B204 is broken'* \n- **Occupancy levels:** *'How busy is the canteen?'*\n\nHow can I help you today?"
        
    return jsonify({
        "message": response_msg,
        "intent": intent,
        "action": action
    })

if __name__ == '__main__':
    # Run the server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
