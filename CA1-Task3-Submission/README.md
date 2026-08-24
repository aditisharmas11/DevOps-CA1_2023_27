# CampusIQ — AI Smart Campus Assistant

> **Think Smart. Campus Smarter.**

CampusIQ is an AI-powered Smart Campus platform that helps students find campus resources, discover available classrooms, report campus problems, and get immediate answers through a natural language AI Copilot. Administrators can monitor classrooms, occupancy density, active events, and maintenance tickets in real-time from a simple, interactive analytics dashboard.

---

## 1. Problem Statement & Solution

### The Problem
Traditional college management portals and campus ERPs are clunky, static, and disjointed. Students face difficulties searching for available study spaces with specific resources (e.g., projectors, AC), locating facilities on campus, tracking daily workshops/events, and reporting facilities failures. Maintenance staff and administrators struggle to classify ticket categories and triage priorities, leading to slow response times.

### The Solution: CampusIQ
CampusIQ turns campus navigation and facilities operations into a cohesive, intelligent ecosystem:
1. **Interactive AI Copilot**: A conversational chat interface that resolves questions about classrooms, locations, and events, while automatically filing maintenance requests on the fly.
2. **Automated Triage**: An AI-based categorization engine that parses maintenance descriptions and instantly flags issues (e.g., HVAC failure vs chair scratch) with categories and priority values (`HIGH`, `MEDIUM`, `LOW`).
3. **IoT Density Hub**: Simulated building and sensor trackers that monitor physical occupancy and log telemetry variables dynamically.

---

## 2. Tech Stack

### Frontend
- **React 18** with **TypeScript** and **Vite**
- **Tailwind CSS v4** (Modern utilities, dark theme toggles, glassmorphic filters)
- **React Router Dom** (Role-based guards and client routing)
- **Axios** (Server requests)
- **Recharts** (Classroom utilization bar graphs & building density area charts)
- **Leaflet + OpenStreetMap** (Interactive campus map with custom status markers)
- **Lucide React** (Vector icons)

### Backend
- **Python 3** with **Flask** & **Flask-Cors**

### Database
- **SQLite 3** (`campus.db`)

### AI Integration
- **Ollama API** with the **Qwen** model
- **Robust Keyword Fallback Parser**: Activates automatically if Ollama is offline/delayed, ensuring 100% demo reliability.

---

## 3. Database Schema

The database uses SQLite (`campus.db`) initialized with the following tables:

1. **`users`**
   - `id`: INTEGER (Primary Key)
   - `email`: TEXT (Unique)
   - `password`: TEXT
   - `name`: TEXT
   - `role`: TEXT (`student` or `admin`)
   
2. **`classrooms`**
   - `id`: INTEGER (Primary Key)
   - `name`: TEXT (Unique)
   - `building`: TEXT
   - `capacity`: INTEGER
   - `occupancy_pct`: INTEGER
   - `projector`: INTEGER (1 = available, 0 = none)
   - `ac`: INTEGER (1 = working, 0 = none)
   - `status`: TEXT (`AVAILABLE`, `OCCUPIED`, `FULL`, `MAINTENANCE`)

3. **`locations`**
   - `id`: INTEGER (Primary Key)
   - `name`: TEXT (Unique)
   - `latitude`: REAL
   - `longitude`: REAL
   - `open_until`: TEXT
   - `occupancy_pct`: INTEGER
   - `study_rooms`: INTEGER
   - `details`: TEXT

4. **`events`**
   - `id`: INTEGER (Primary Key)
   - `title`: TEXT
   - `date`: TEXT (YYYY-MM-DD)
   - `time`: TEXT (HH:MM AM/PM)
   - `location`: TEXT
   - `category`: TEXT (`Technical`, `Cultural`, `Sports`, `Workshop`, `Club`)
   - `description`: TEXT

5. **`maintenance`**
   - `id`: INTEGER (Primary Key)
   - `ticket_no`: TEXT (Unique)
   - `issue_type`: TEXT
   - `location`: TEXT
   - `description`: TEXT
   - `priority`: TEXT (`LOW`, `MEDIUM`, `HIGH`)
   - `status`: TEXT (`OPEN`, `IN PROGRESS`, `RESOLVED`)
   - `created_at`: TEXT
   - `category`: TEXT (`HVAC`, `IT`, `Plumbing`, `Furniture`, `Cleanliness`, `Electrical`, `Other`)

6. **`occupancy`**
   - `id`: INTEGER (Primary Key)
   - `building_name`: TEXT (Unique)
   - `occupancy_pct`: INTEGER
   - `updated_at`: TEXT

---

## 4. API Reference

| Endpoint | Method | Description |
|---|---|---|
| `POST /api/login` | POST | Authenticate user role and credentials |
| `POST /api/register` | POST | Register new student or admin |
| `GET /api/classrooms` | GET | Retrieve classrooms list (supports query filters) |
| `GET /api/classrooms/<id>` | GET | Fetch single classroom details |
| `GET /api/locations` | GET | Fetch Leaflet coordinates and open hours |
| `GET /api/events` | GET | Retrieve upcoming and past campus activities |
| `GET /api/maintenance` | GET | Fetch maintenance ticket logs |
| `POST /api/maintenance` | POST | Report issue (AI classifies category & priority) |
| `PUT /api/maintenance/<id>` | PUT | Advance ticket status (OPEN -> IN PROGRESS -> RESOLVED) |
| `GET /api/occupancy` | GET | Fetch building densities |
| `POST /api/occupancy/simulate` | POST | Perturb building occupancies randomly |
| `GET /api/sensors` | GET | Fetch virtual sensor readings |
| `POST /api/sensors/simulate` | POST | Perturb sensor metrics randomly |
| `POST /api/copilot` | POST | Query AI agent with prompt |

---

## 5. Setup & Running Instructions

### Backend Setup
1. Open a terminal and navigate to the project directory:
   ```bash
   cd "C:\Desktop\SYMBI\SEM 7\DevOps\CA1\Project"
   ```
2. Install Python dependencies:
   ```bash
   pip install --user -r backend/requirements.txt
   ```
3. Initialize the SQLite database and seed initial mock values:
   ```bash
   python backend/database.py
   ```
4. Run the Flask development server:
   ```bash
   python backend/app.py
   ```
   *The backend will boot on `http://localhost:5000`.*

### Frontend Setup
1. Open a second terminal window.
2. Navigate to the frontend directory:
   ```bash
   cd "C:\Desktop\SYMBI\SEM 7\DevOps\CA1\Project\frontend"
   ```
3. Install node dependencies:
   ```bash
   npm install
   ```
4. Start the Vite React development server:
   ```bash
   npm run dev
   ```
   *Open your browser and navigate to `http://localhost:5173` to view the application.*

---

## 6. Ollama & Qwen Integration

CampusIQ integrates Ollama running locally.
1. Download and install [Ollama](https://ollama.com).
2. Download the Qwen model in your terminal:
   ```bash
   ollama run qwen
   ```
3. Ensure Ollama is running in the background. The app will communicate with the API on `http://localhost:11434`.
4. **Fallback Mode**: If Ollama is offline or takes too long to respond, the backend automatically activates the keyword matching processor. The chatbot and classification systems will continue working seamlessly during your presentation.

---

## 7. Demo Accounts & Credentials

Use these credentials to log in during presentations:

### Student Role
- **Email**: `student@campusiq.com`
- **Password**: `student123`

### Admin Role
- **Email**: `admin@campusiq.com`
- **Password**: `admin123`

---

## 8. Hackathon Presentation Workflow (3–5 Minutes)

Follow this path for a flawless demonstration:

1. **Dashboard & Overview (1 min)**:
   - Access `http://localhost:5173`.
   - Log in as the **Student** (`student@campusiq.com`).
   - Show the dynamic welcome panel ("Good Morning Alex 👋") and stats grid populated directly from SQLite.
2. **AI Copilot Classroom Finder (1 min)**:
   - Click **AI Copilot** or navigate to `/copilot`.
   - Ask the copilot: *"Find me a classroom for 40 students with a projector."*
   - The AI / Fallback processor queries SQLite and outputs **B204** with its specs.
   - Click the embedded **View B204 on Map** action button.
3. **Interactive Map Highlight (0.5 min)**:
   - The app navigates to `/map`, focuses the view on **Block B**, triggers a zoom, opens B204's popup, and highlights the location.
4. **Filing a Maintenance Ticket (1 min)**:
   - Go to Copilot or the Maintenance tab.
   - Report: *"The AC in B204 is broken."*
   - The backend runs classification, logs the category as **HVAC**, priority as **HIGH**, and returns the new ticket number (e.g. `Ticket #CIQ-1042`).
5. **Admin Operations Desk (1 min)**:
   - Log out and log in as the **Admin** (`admin@campusiq.com`).
   - Navigate to `/admin` to view charts (Recharts Classroom Utilization & Campus Occupancy).
   - In the Maintenance Queue, see Ticket `CIQ-1042` marked as **HIGH** and **OPEN**.
   - Click **Advance** to transition status from `OPEN` → `IN PROGRESS` → `RESOLVED`.
   - Go to the **Occupancy** or **Sensors** tabs, click **Simulate Update**, and watch the charts and values refresh instantly!

---

## 9. Future Scope

- **Indoor Navigation**: Integrate building floor plans to guide students to specific rooms inside blocks.
- **Physical IoT Integration**: Replace simulated sensors with ESP32 microcontrollers communicating via WebSockets.
- **Calendar Integrations**: Automatically sync classroom bookings and workshop schedules with Google Calendar and Microsoft Outlook.
