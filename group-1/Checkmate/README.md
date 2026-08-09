# DevOps CA1 - Open Source Contribution Report

## 👥 Group Information (Group 1)
- **Class / Division**: DevOps TH1
- **Target Open Source Project**: [bluewave-labs/Checkmate](https://github.com/bluewave-labs/Checkmate)
- **Target Issue**: [#2679 - Maintenance Mode for Status Pages & Monitors](https://github.com/bluewave-labs/Checkmate/issues/2679)
- **Checkmate PR**: [Link to your Checkmate PR]

### Group Members
| Roll No / PRN | Name | Class / Batch |
|---|---|---|
| **23070122100** | Harsh Ledwani | TH1 |
| **23070122113** | Shivam Kapure | TH1 |
| **23070122114** | Kashyup Gaud | TH1 |

---

## 🔍 What is Checkmate?
**Checkmate** is a modern, self-hosted, open-source infrastructure monitoring and public status page platform. It provides:
- **Multi-protocol Uptime Monitoring**: HTTP(S), TCP Port, Ping (ICMP), DNS, gRPC, WebSocket, Docker containers, and Game servers.
- **Customizable Public & Private Status Pages**: Multi-theme status pages (`Modern`, `Refined`, `Bold`, `Editorial`, `Minimal`) with customizable domains, custom CSS, and subscriber notifications.
- **Incident & Maintenance Management**: Scheduled maintenance windows, incident response workflows, and multi-channel alerting (Slack, Discord, Email, PagerDuty, Webhooks, Telegram, Twilio, etc.).

---

## 🎯 Contribution Overview & Problem Statement
In Checkmate, when services or monitors were placed into scheduled maintenance windows, public status pages and monitor detail pages did not reflect this status to external visitors and operations teams.

Our group implemented end-to-end **Maintenance Mode Visibility** across both frontend status page themes and backend API service layers:
1. Displays an active **`MaintenanceBanner`** on public status pages detailing which monitors are in maintenance and the estimated completion time (ETA).
2. Displays an active maintenance warning banner on the individual **Monitor Details** view (`Uptime/Details`).
3. Backend service logic calculates exact expiration times for both one-time and recurring (cron/interval) maintenance schedules.

---

## 🚀 Key Deliverables & Technical Implementation

### 1. Frontend Architecture (`client`)
- **`MaintenanceBanner.tsx`**: Built a modular, responsive banner rendered seamlessly across all 5 status page themes (`Modern`, `Refined`, `Bold`, `Editorial`, `Minimal`).
- **Real-Time Duration & Monitor Mapping**: Dynamically formats human-readable remaining time (e.g. `Ends in ~45 minutes`) and lists affected monitor names.
- **Monitor Detail Page (`Uptime/Details`)**: Injected an active maintenance warning card when the viewed monitor is under an ongoing maintenance window.
- **Internationalization (`i18n`)**: Added localized translation keys to `client/src/locales/en.json`.

### 2. Backend Services (`server`)
- **`maintenanceWindow.ts`**: Implemented `getActiveWindowEnd()` utility to compute window termination timestamps across recurring and one-time maintenance windows.
- **`StatusPageService`**: Updated `getPublicStatusPagePayload` to query `IMaintenanceWindowsRepository` for active windows covering status page monitors.
- **Dependency Injection**: Injected `IMaintenanceWindowsRepository` into `StatusPageService` via `server/src/config/services.api.ts`.

### 3. Testing & Type Safety
- Added unit tests for `maintenanceWindow.ts` and `statusPageService.test.ts`.
- Verified system integrity with all **67 unit test suites (1,262 tests) passing**.

---

## 📁 Key Files Modified / Added
```
group-1/Checkmate/
├── client/
│   ├── src/Pages/StatusPage/Status/themes/shared/MaintenanceBanner.tsx  # [NEW] Maintenance Banner component
│   ├── src/Pages/StatusPage/Status/themes/shared/BaseStatusPage.tsx      # Integrated banner in status pages
│   ├── src/Pages/StatusPage/Status/index.tsx                             # Props mapping
│   ├── src/Pages/Uptime/Details/index.tsx                                # Monitor detail page alert
│   ├── src/Types/StatusPage.ts                                           # TypeScript interfaces
│   └── src/locales/en.json                                               # i18n localization tokens
└── server/
    ├── src/config/services.api.ts                                        # Repo dependency injection
    ├── src/domain/status-pages/status-page.service.ts                    # Payload maintenance querying
    ├── src/domain/status-pages/status-page.type.ts                       # Backend type definitions
    ├── src/utils/maintenanceWindow.ts                                    # End-time calculation logic
    ├── test/unit/services/statusPageService.test.ts                      # Unit tests
    └── test/unit/utils/maintenanceWindow.test.ts                         # Unit tests
```

---

## 🛠️ Prerequisites & Dependencies

### System Requirements
- **Node.js**: `v20.x` or later
- **npm**: `v10.x` or later
- **MongoDB**: `v6.x` or later (Local or MongoDB Atlas)
- **Redis**: `v7.x` or later (Local or Redis Cloud)
- **Docker & Docker Compose** *(Optional, for containerized run)*

---

## 🏃 How to Run Locally

### 1. Start Database & Redis (Docker)
If you have Docker installed, start MongoDB and Redis with a single command:
```bash
docker run -d --name checkmate-mongo -p 27017:27017 mongo:7
docker run -d --name checkmate-redis -p 6379:6379 redis:7-alpine
```

### 2. Backend Setup (`server`)
```bash
cd server

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env

# Run development server
npm run dev
```
Backend API will start on `http://localhost:3000`.

### 3. Frontend Setup (`client`)
```bash
cd client

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env

# Run development server
npm run dev
```
Frontend UI will start on `http://localhost:5173`.

---

## 🧪 Running Tests & Quality Checks

### Backend Unit Tests
```bash
cd server
npm run test:unit
```

### TypeScript Validation & Linting
```bash
# Server
cd server
npx tsc --noEmit
npm run lint

# Client
cd client
npm run lint
npm run build
```
