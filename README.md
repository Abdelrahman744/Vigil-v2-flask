<p align="center">
  <img src="https://img.shields.io/badge/Vigil-v2.0-blueviolet?style=for-the-badge" alt="Vigil Badge"/>
  <img src="https://img.shields.io/badge/Flask-3.1-green?style=for-the-badge&logo=flask" alt="Flask Badge"/>
  <img src="https://img.shields.io/badge/React-18-blue?style=for-the-badge&logo=react" alt="React Badge"/>
  <img src="https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite" alt="SQLite Badge"/>
</p>

# 🛡️ Vigil — Website Uptime Monitoring System

> **Vigil** is a full-stack website uptime monitoring platform that allows registered users to track the availability of any URL. When a target is added, the system immediately pings the website and records its **status** (Up / Down), **HTTP status code**, and **response time**. Users can view real-time stats such as **availability percentage** and **average latency**, browse full check-history logs, and manage their monitored sites — all through a modern React dashboard backed by a Flask REST API.

---

## 📑 Table of Contents

- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Entity-Relationship Diagram (ERD)](#-entity-relationship-diagram-erd)
- [Data Flow Diagrams (DFD)](#-data-flow-diagrams-dfd)
- [System Architecture](#-system-architecture)
- [Database Schema](#-database-schema)
- [API Documentation](#-api-documentation)
- [Frontend Pages](#-frontend-pages)
- [Getting Started](#-getting-started)
- [License](#-license)

---

## 🛠 Technology Stack

| Layer      | Technology                                     |
|------------|-------------------------------------------------|
| Frontend   | React 18, Tailwind CSS v4, Vite, Framer Motion |
| Backend    | Python 3.12, Flask 3.1, SQLAlchemy              |
| Database   | SQLite 3 (file-based relational DB)             |
| Auth       | JWT (PyJWT) with Bearer Tokens                  |
| Monitoring | Python `requests` library (HTTP pinging)        |

---

## 📁 Project Structure

```
Vigil-v2-flask/
├── backend/
│   ├── app/
│   │   ├── __init__.py             # Flask Application Factory
│   │   ├── models.py               # SQLAlchemy Database Models (User, Target, Log)
│   │   ├── utils.py                # Monitoring helpers (pings), auth decorators & JWT helpers
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py             # Auth Blueprint (register, login, logout)
│   │       ├── targets.py          # Target Blueprint (CRUD + manual ping)
│   │       └── monitor.py          # Monitor Blueprint (cron heartbeat check)
│   ├── config.py                   # Centralised configuration
│   ├── run.py                      # Development server entry point
│   └── requirements.txt            # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api.js                  # Axios client with JWT interceptor
│   │   ├── App.jsx                 # Router & protected routes
│   │   ├── main.jsx                # React entry point
│   │   ├── index.css               # Vanilla CSS styling & themes
│   │   └── pages/
│   │       ├── Login.jsx           # Login page
│   │       ├── Register.jsx        # Register page (email-uniqueness check)
│   │       └── Dashboard.jsx       # Interactive real-time monitoring dashboard
│   ├── vite.config.js              # Vite bundler config
│   └── package.json                # Node dependencies
├── .gitignore
└── README.md
```

---

## 🗃 Entity-Relationship Diagram (ERD)

The application uses **3 normalized tables** with the following relationships:

- A **User** can own many **Targets** (one-to-many).
- A **Target** can have many **Logs** (one-to-many, cascade delete).
- The `url` column is **NOT** globally unique — a composite unique constraint on `(user_id, url)` ensures each user cannot track a duplicate URL, while different users can independently monitor the same website.

```mermaid
erDiagram
    USER ||--o{ TARGET : "owns"
    TARGET ||--o{ LOG : "has"

    USER {
        int id PK
        string username
        string email UK "Unique"
        string password_hash
    }

    TARGET {
        int id PK
        string name
        string url
        string status "Up / Down / Pending"
        int user_id FK "References User.id"
    }

    LOG {
        int id PK
        int target_id FK "References Target.id"
        datetime timestamp
        string status "Up / Down"
        int response_time "Milliseconds"
        int status_code "HTTP code e.g. 200"
        text error_message "Null if healthy"
        text details "Human-readable summary"
    }
```

---

## 📊 Data Flow Diagrams (DFD)

### Level 0 — Context Diagram

Shows the system as a single process interacting with the external user, external websites, and the database.

```mermaid
graph LR
    subgraph External
        U["👤 User (Browser)"]
        W["🌐 External Websites"]
    end

    subgraph "Vigil System"
        API["🛡️ Vigil Flask API"]
    end

    subgraph Storage
        DB[("📦 SQLite Database")]
    end

    U -- "Register / Login" --> API
    U -- "Add / Delete / List / Ping Targets" --> API
    U -- "View Logs & Stats" --> API
    API -- "JWT Token" --> U
    API -- "JSON Responses" --> U
    API -- "HTTP Ping" --> W
    W -- "Status Code + Latency" --> API
    API -- "Read / Write" --> DB
```

### Level 1 — Process Decomposition

Breaks down the system into its three core subsystems showing data flows between each process and the database tables.

```mermaid
graph TB
    User["👤 User"]
    Web["🌐 External Website"]

    subgraph "1.0 Authentication"
        P1["1.1 Register"]
        P2["1.2 Login"]
        P3["1.3 Logout"]
    end

    subgraph "2.0 Target Management"
        P4["2.1 List Targets + Stats"]
        P5["2.2 Add Target + Ping"]
        P6["2.3 Delete Target"]
        P7["2.4 Get Target Logs"]
        P8["2.5 Manual Ping"]
    end

    subgraph "3.0 Monitoring"
        P9["3.1 Cron Heartbeat"]
    end

    DB_User[("User Table")]
    DB_Target[("Target Table")]
    DB_Log[("Log Table")]

    User -->|"credentials"| P1
    User -->|"credentials"| P2
    User -->|"token"| P3

    P1 -->|"INSERT"| DB_User
    P1 -->|"JWT token"| User
    P2 -->|"SELECT"| DB_User
    P2 -->|"JWT token"| User

    User -->|"auth request"| P4
    User -->|"name, url"| P5
    User -->|"target_id"| P6

    P4 -->|"SELECT + stats"| DB_Target
    P4 -->|"SELECT all"| DB_Log
    P4 -->|"target list + stats"| User

    P5 -->|"INSERT"| DB_Target
    P5 -->|"HTTP GET"| Web
    Web -->|"status + latency"| P5
    P5 -->|"INSERT check result"| DB_Log
    P5 -->|"new target + ping result"| User

    P6 -->|"DELETE cascade"| DB_Target
    P6 -->|"DELETE"| DB_Log
    P6 -->|"confirmation"| User

    User -->|"target_id"| P7
    P7 -->|"SELECT"| DB_Log
    P7 -->|"log history"| User

    User -->|"target_id"| P8
    P8 -->|"HTTP GET"| Web
    Web -->|"status + latency"| P8
    P8 -->|"INSERT check result"| DB_Log
    P8 -->|"UPDATE target status"| DB_Target
    P8 -->|"ping result"| User

    P9 -->|"SELECT all"| DB_Target
    P9 -->|"HTTP GET each"| Web
    Web -->|"status + latency"| P9
    P9 -->|"INSERT results"| DB_Log
    P9 -->|"UPDATE target status"| DB_Target
```

---

## 🏗 System Architecture

```mermaid
graph TB
    Browser["🌐 Browser"]
    CronJob["⏱️ External Cron Job"]

    subgraph "Frontend (localhost:5173)"
        Login["Login Page"]
        Register["Register Page"]
        Dashboard["Dashboard Page"]
    end

    subgraph "Backend (localhost:5000)"
        Auth["Auth Module<br/>Register / Login / Logout"]
        Targets["Target Module<br/>CRUD + Stats + Manual Ping"]
        Monitor["Monitor Module<br/>Cron Heartbeat"]
    end

    subgraph "Database"
        DB[("SQLite<br/>vigil.db")]
    end

    subgraph "External"
        Web["🌐 Monitored<br/>Websites"]
    end

    Browser --> Login
    Browser --> Register
    Browser --> Dashboard
    CronJob -->|"GET /api/cron/heartbeat"| Monitor

    Login -->|"POST /api/login"| Auth
    Register -->|"POST /api/register"| Auth
    Dashboard -->|"POST /api/logout"| Auth
    Dashboard -->|"GET /api/targets"| Targets
    Dashboard -->|"POST /api/targets"| Targets
    Dashboard -->|"DELETE /api/targets/id"| Targets
    Dashboard -->|"GET /api/targets/id/logs"| Targets
    Dashboard -->|"POST /api/targets/id/ping"| Targets

    Auth -->|"Read / Write"| DB
    Targets -->|"Read / Write"| DB
    Targets -->|"HTTP GET (Pings)"| Web
    Monitor -->|"Read / Write"| DB
    Monitor -->|"HTTP GET (Pings)"| Web
```

---

## 🗃 Database Schema

| Table    | Columns                                                                                              | Constraints                            |
|----------|------------------------------------------------------------------------------------------------------|----------------------------------------|
| `User`   | `id` PK, `username`, `email` UNIQUE, `password_hash`                                         | Primary entity                         |
| `Target` | `id` PK, `name`, `url`, `status`, `user_id` FK                                                      | Composite UNIQUE (`user_id`, `url`)    |
| `Log`    | `id` PK, `target_id` FK, `timestamp`, `status`, `response_time`, `status_code`, `error_message`, `details` | Cascade delete with Target             |

---

## 📡 API Documentation

**Base URL:** `http://localhost:5000`

### Authentication Endpoints

| # | Method | Endpoint          | Auth?  | Description                    | Request Body                          |
|---|--------|-------------------|--------|--------------------------------|---------------------------------------|
| 1 | POST   | `/api/register`   | ❌ No  | Register a new user            | `{ "username", "email", "password" }` |
| 2 | POST   | `/api/login`      | ❌ No  | Login and receive JWT token    | `{ "email", "password" }`             |
| 3 | POST   | `/api/logout`     | ✅ Yes | Invalidate current JWT token   | —                                     |

### Target Endpoints

| # | Method | Endpoint                  | Auth?  | Description                                  | Request Body          |
|---|--------|---------------------------|--------|----------------------------------------------|-----------------------|
| 4 | GET    | `/api/targets`            | ✅ Yes | List all targets with stats & availability   | —                     |
| 5 | POST   | `/api/targets`            | ✅ Yes | Add target & perform immediate health check  | `{ "name", "url" }`  |
| 6 | DELETE | `/api/targets/<id>`       | ✅ Yes | Delete a target and all its logs             | —                     |

### Log & Monitoring Endpoints

| # | Method | Endpoint                      | Auth?  | Description                                    | Request Body    |
|---|--------|-------------------------------|--------|------------------------------------------------|-----------------|
| 7 | GET    | `/api/targets/<id>/logs`      | ✅ Yes | Retrieve full check history for a target       | —               |
| 8 | POST   | `/api/targets/<id>/ping`      | ✅ Yes | Manually ping a tracked target (saves to DB)  | —               |
| 9 | GET    | `/api/cron/heartbeat`         | ❌ No  | Batch-check all targets (background job)       | —               |

### Authentication Header

All protected endpoints require:
```
Authorization: Bearer <your_jwt_token>
```

### Response Examples

<details>
<summary><strong>POST /api/register — 201 Created</strong></summary>

```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "data": {
    "user": {
      "id": 1,
      "username": "abdelrahman",
      "email": "admin@vigil.com"
    }
  }
}
```
</details>

<details>
<summary><strong>POST /api/login — 200 OK</strong></summary>

```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```
</details>

<details>
<summary><strong>POST /api/logout — 200 OK</strong></summary>

```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```
</details>

<details>
<summary><strong>GET /api/targets — 200 OK (with stats)</strong></summary>

```json
{
  "count": 1,
  "targets": [
    {
      "id": 1,
      "name": "Google",
      "url": "https://google.com",
      "status": "Up",
      "user_id": 1,
      "last_checked": "2026-05-03T18:38:33",
      "stats": {
        "totalChecks": 1,
        "upChecks": 1,
        "downChecks": 0,
        "availability": "100.0%",
        "averageLatency": "1540.0"
      }
    }
  ]
}
```
</details>

<details>
<summary><strong>POST /api/targets — 201 Created (with initial ping)</strong></summary>

```json
{
  "id": 1,
  "name": "Google",
  "url": "https://google.com",
  "status": "Up",
  "user_id": 1,
  "initial_check": {
    "status": "Up",
    "response_time": 1540,
    "status_code": 200,
    "error_message": null,
    "details": "Check completed in 1540ms (Status: 200)"
  }
}
```
</details>

<details>
<summary><strong>DELETE /api/targets/1 — 200 OK</strong></summary>

```json
{
  "status": "success",
  "message": "Target deleted successfully"
}
```
</details>

<details>
<summary><strong>GET /api/targets/1/logs — 200 OK</strong></summary>

```json
{
  "target": { "id": 1, "name": "Google", "url": "https://google.com" },
  "count": 1,
  "logs": [
    {
      "id": 1,
      "timestamp": "2026-05-03T18:38:33",
      "status": "Up",
      "response_time": 1540,
      "status_code": 200,
      "error_message": null,
      "details": "Check completed in 1540ms (Status: 200)"
    }
  ]
}
```
</details>

<details>
<summary><strong>POST /api/targets/&lt;id&gt;/ping — 200 OK</strong></summary>

```json
{
  "status": "success",
  "message": "Ping Up",
  "data": {
    "status": "Up",
    "response_time": 312,
    "status_code": 200,
    "error_message": null,
    "details": "Check completed in 312ms (Status: 200)"
  }
}
```
</details>

---

## 🖥 Frontend Pages

The React frontend consumes all API endpoints listed above.

| Page        | Route         | Endpoints Used                              |
|-------------|---------------|---------------------------------------------|
| **Login**   | `/login`      | `POST /api/login`                           |
| **Register**| `/register`   | `POST /api/register`                        |
| **Dashboard** | `/dashboard` | `POST /api/logout`, `GET /api/targets`, `POST /api/targets`, `DELETE /api/targets/<id>`, `GET /api/targets/<id>/logs`, `POST /api/targets/<id>/ping` |

**Total: 8 endpoints used across the frontend (all core).**

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+** and **Node.js 18+** installed
- **Git** for cloning the repository

### Run Locally

```bash
# Clone
git clone https://github.com/Abdelrahman744/Vigil-v2-flask.git
cd Vigil-v2-flask

# Backend (Terminal 1)
cd backend
python -m pip install -r requirements.txt
python run.py

# Frontend (Terminal 2)
cd frontend
npm install
npm run dev
```

- **Backend API:** http://localhost:5000
- **Frontend UI:** http://localhost:5173

> **Note:** When running the backend via `python run.py`, a background thread automatically starts. It triggers the `/api/cron/heartbeat` endpoint every 60 seconds and logs the real-time status of all your tracked targets directly in the terminal, simulating a production cron job!

---

## 📄 License

This project is developed for academic purposes as part of a university software engineering course. All rights reserved.

---

<p align="center">
  <strong>Built with ❤️ by the Vigil Team</strong>
</p>