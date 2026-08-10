import sqlite3
import os
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "campus.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS classrooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        building TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        occupancy_pct INTEGER NOT NULL,
        projector INTEGER NOT NULL, -- 1 for true/available, 0 for false
        ac INTEGER NOT NULL,        -- 1 for working/available, 0 for false
        status TEXT NOT NULL        -- AVAILABLE, OCCUPIED, FULL, MAINTENANCE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        open_until TEXT NOT NULL,
        occupancy_pct INTEGER NOT NULL,
        study_rooms INTEGER NOT NULL,
        details TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        date TEXT NOT NULL, -- YYYY-MM-DD
        time TEXT NOT NULL, -- HH:MM AM/PM
        location TEXT NOT NULL,
        category TEXT NOT NULL, -- Technical, Cultural, Sports, Workshop, Club
        description TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_no TEXT UNIQUE NOT NULL,
        issue_type TEXT NOT NULL,
        location TEXT NOT NULL,
        description TEXT NOT NULL,
        priority TEXT NOT NULL, -- LOW, MEDIUM, HIGH
        status TEXT NOT NULL,   -- OPEN, IN PROGRESS, RESOLVED
        created_at TEXT NOT NULL,
        category TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS occupancy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        building_name TEXT UNIQUE NOT NULL,
        occupancy_pct INTEGER NOT NULL,
        updated_at TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

def seed_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing data to allow fresh seeds if run multiple times
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM classrooms")
    cursor.execute("DELETE FROM locations")
    cursor.execute("DELETE FROM events")
    cursor.execute("DELETE FROM maintenance")
    cursor.execute("DELETE FROM occupancy")

    # 1. Seed Users
    users_data = [
        ("student@campusiq.com", "student123", "Alex Mercer", "student"),
        ("admin@campusiq.com", "admin123", "Sarah Connor", "admin")
    ]
    cursor.executemany(
        "INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)",
        users_data
    )

    # 2. Seed Classrooms (20 rooms across 3 blocks)
    classrooms_data = [
        # Block B (includes B204 requested in hackathon)
        ("B204", "Block B", 60, 10, 1, 1, "AVAILABLE"),
        ("B205", "Block B", 40, 80, 1, 1, "OCCUPIED"),
        ("B206", "Block B", 30, 0, 0, 0, "AVAILABLE"),
        ("B101", "Block B", 120, 95, 1, 1, "FULL"),
        ("B102", "Block B", 80, 0, 1, 0, "MAINTENANCE"),
        ("B201", "Block B", 50, 45, 1, 1, "AVAILABLE"),
        ("B202", "Block B", 45, 100, 0, 1, "FULL"),
        
        # Block A
        ("A101", "Block A", 50, 15, 1, 1, "AVAILABLE"),
        ("A102", "Block A", 45, 60, 1, 0, "AVAILABLE"),
        ("A103", "Block A", 30, 80, 0, 1, "OCCUPIED"),
        ("A201", "Block A", 100, 90, 1, 1, "OCCUPIED"),
        ("A202", "Block A", 60, 0, 1, 1, "AVAILABLE"),
        ("A203", "Block A", 40, 0, 0, 0, "AVAILABLE"),
        
        # Block C
        ("C101", "Block C", 150, 85, 1, 1, "OCCUPIED"),
        ("C102", "Block C", 75, 40, 1, 0, "AVAILABLE"),
        ("C103", "Block C", 50, 0, 0, 1, "MAINTENANCE"),
        ("C201", "Block C", 80, 20, 1, 1, "AVAILABLE"),
        ("C202", "Block C", 40, 100, 1, 1, "FULL"),
        ("C203", "Block C", 30, 10, 0, 1, "AVAILABLE"),
        ("C204", "Block C", 60, 50, 1, 1, "AVAILABLE")
    ]
    cursor.executemany(
        "INSERT INTO classrooms (name, building, capacity, occupancy_pct, projector, ac, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        classrooms_data
    )

    # 3. Seed Locations (10 locations for Leaflet)
    # Using fictional offsets around Pune/Symbiosis style base coordinates: [18.5204, 73.8567]
    locations_data = [
        ("Main Gate", 18.5180, 73.8540, "11:59 PM", 20, 0, "Main entry/exit point of the campus. Security desk open 24/7."),
        ("Block A", 18.5210, 73.8545, "09:00 PM", 82, 5, "Academic building housing Humanities, Business, and Admin departments."),
        ("Block B", 18.5215, 73.8565, "09:30 PM", 52, 8, "Engineering and Science labs. Equipped with state-of-the-art facilities."),
        ("Block C", 18.5205, 73.8580, "09:00 PM", 35, 6, "Management and Design departments, classrooms and common rooms."),
        ("Library", 18.5200, 73.8560, "10:00 PM", 72, 4, "Central Digital Library. Quiet study rooms, computers, and database access."),
        ("Canteen", 18.5195, 73.8550, "08:30 PM", 64, 0, "Main food court serving multi-cuisine meals and coffee counters."),
        ("Seminar Hall", 18.5220, 73.8555, "08:00 PM", 10, 2, "Auditorium for workshops, guest lectures, and cultural presentations."),
        ("Sports Ground", 18.5190, 73.8575, "09:00 PM", 30, 0, "Football field, running track, basketball courts, and sports locker rooms."),
        ("Parking", 18.5185, 73.8555, "11:59 PM", 45, 0, "Multi-level parking facility for students, faculty, and visitors."),
        ("Medical Center", 18.5200, 73.8545, "06:00 PM", 15, 1, "First-aid, nurse on duty, counseling sessions, and basic medical checkups.")
    ]
    cursor.executemany(
        "INSERT INTO locations (name, latitude, longitude, open_until, occupancy_pct, study_rooms, details) VALUES (?, ?, ?, ?, ?, ?, ?)",
        locations_data
    )

    # 4. Seed Events (Dynamic dates: 3 today, some future/past)
    today_str = date.today().isoformat()
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()

    events_data = [
        # Today's events (as in user request)
        ("AI Workshop", today_str, "04:00 PM", "Seminar Hall", "Workshop", "Hands-on session on large language models and prompt engineering."),
        ("Coding Club Meetup", today_str, "06:00 PM", "Block B", "Club", "Weekly competitive programming discussions and project review."),
        ("Football Match", today_str, "07:00 PM", "Sports Ground", "Sports", "Inter-departmental semi-finals: Tech vs Management."),
        
        # Tomorrow's events
        ("Career Fair 2026", tomorrow_str, "10:00 AM", "Seminar Hall", "Technical", "Annual recruitment drive hosting top-tier tech and consulting firms."),
        ("Acoustic Music Night", tomorrow_str, "06:30 PM", "Canteen", "Cultural", "An evening of live unplugged music performances by student bands."),
        ("Yoga and Mindfulness", tomorrow_str, "07:00 AM", "Sports Ground", "Sports", "Morning wellness session led by guest instructor."),
        
        # Past events
        ("Web3 Hackathon", yesterday_str, "09:00 AM", "Block B", "Technical", "24-hour hackathon focusing on decentralized applications and smart contracts."),
        ("Design Thinking Panel", yesterday_str, "02:00 PM", "Block C", "Workshop", "Interactive discussion on UI/UX practices and prototype designing.")
    ]
    cursor.executemany(
        "INSERT INTO events (title, date, time, location, category, description) VALUES (?, ?, ?, ?, ?, ?)",
        events_data
    )

    # 5. Seed Maintenance Tickets (15 tickets)
    maintenance_data = [
        ("CIQ-1001", "AC problems", "B204", "AC in B204 is making an extremely loud noise and not cooling.", "MEDIUM", "IN PROGRESS", yesterday_str, "HVAC"),
        ("CIQ-1002", "Wi-Fi issues", "A103", "Wi-Fi signals are extremely weak in the corner seats.", "MEDIUM", "IN PROGRESS", yesterday_str, "IT"),
        ("CIQ-1003", "Plumbing", "Block C", "Water leakage from faucet in ground floor restrooms.", "LOW", "RESOLVED", yesterday_str, "Plumbing"),
        ("CIQ-1004", "Electricity issues", "Block A", "Corridor lights near A202 are flickering constantly.", "MEDIUM", "RESOLVED", yesterday_str, "Electrical"),
        ("CIQ-1005", "Projector problems", "C102", "Projector display is blurred and colors are distorted.", "LOW", "OPEN", today_str, "IT"),
        ("CIQ-1006", "Furniture", "B102", "Three writing pads are broken on chairs in the middle row.", "LOW", "OPEN", today_str, "Furniture"),
        ("CIQ-1007", "Cleanliness", "Canteen", "Spill near food counter needs immediate cleanup.", "LOW", "RESOLVED", today_str, "Cleanliness"),
        ("CIQ-1008", "Fan problems", "B206", "Ceiling fan at the back does not rotate, hums loudly.", "LOW", "OPEN", today_str, "Electrical"),
        ("CIQ-1009", "AC problems", "A102", "Thermostat display shows error code E5 and system is shut down.", "HIGH", "OPEN", today_str, "HVAC"),
        ("CIQ-1010", "Wi-Fi issues", "Library", "Frequent disconnections on CampusSecure network.", "HIGH", "IN PROGRESS", today_str, "IT"),
        ("CIQ-1011", "Electricity issues", "Seminar Hall", "Main stage spot-light bulb needs replacement.", "LOW", "OPEN", today_str, "Electrical"),
        ("CIQ-1012", "Cleanliness", "Block B", "Trash bin overflow at second floor staircase.", "LOW", "OPEN", today_str, "Cleanliness"),
        ("CIQ-1013", "Plumbing", "Block A", "Water purifier filter replacement warning indicator is red.", "MEDIUM", "OPEN", today_str, "Plumbing"),
        ("CIQ-1014", "Furniture", "A101", "Lectern height adjustment lever is stuck.", "LOW", "OPEN", today_str, "Furniture"),
        ("CIQ-1015", "AC problems", "C103", "Complete compressor failure, room is unusable.", "HIGH", "OPEN", today_str, "HVAC")
    ]
    cursor.executemany(
        "INSERT INTO maintenance (ticket_no, issue_type, location, description, priority, status, created_at, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        maintenance_data
    )

    # 6. Seed Occupancy Records (Current building occupancies)
    occupancy_data = [
        ("Block A", 82, datetime.now().isoformat()),
        ("Block B", 52, datetime.now().isoformat()),
        ("Block C", 35, datetime.now().isoformat()),
        ("Library", 72, datetime.now().isoformat()),
        ("Canteen", 64, datetime.now().isoformat())
    ]
    cursor.executemany(
        "INSERT INTO occupancy (building_name, occupancy_pct, updated_at) VALUES (?, ?, ?)",
        occupancy_data
    )

    conn.commit()
    conn.close()
    print("Database successfully initialized and seeded.")

if __name__ == "__main__":
    init_db()
    seed_db()
