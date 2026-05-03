<p align="center">
  <img src="https://img.shields.io/badge/Vigil-v2.0-blueviolet?style=for-the-badge" alt="Vigil Badge"/>
  <img src="https://img.shields.io/badge/Flask-3.1-green?style=for-the-badge&logo=flask" alt="Flask Badge"/>
  <img src="https://img.shields.io/badge/React-18-blue?style=for-the-badge&logo=react" alt="React Badge"/>
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker" alt="Docker Badge"/>
</p>

# 🛡️ Vigil — Website Uptime Monitoring System

> **Vigil** is a full-stack website uptime monitoring platform that allows registered users to track the availability of any URL. It provides real-time status tracking, historical check logs, and a clean dashboard — all powered by a Flask REST API backend with SQLite and a React + Tailwind CSS frontend.

---

## 📑 Table of Contents

- [Team Members](#-team-members)
- [Project Architecture](#-project-architecture)
- [Technology Stack](#-technology-stack)
- [Database Schema (ERD)](#-database-schema-erd)
- [API Documentation](#-api-documentation)
- [Getting Started](#-getting-started)
- [Docker Setup](#-docker-setup)
- [Project Structure](#-project-structure)
- [License](#-license)

---

## 👥 Team Members

| #  | Name                        | Role                  | ID          |
|----|-----------------------------|-----------------------|-------------|
| 1  | Abdelrahman Mohamed Ahmed   | Team Lead / Backend   | 20220302    |
| 2  | Omar Khaled Hassan          | Frontend Developer    | 20220188    |
| 3  | Youssef Ali Ibrahim         | Backend Developer     | 20220415    |
| 4  | Nour ElDin Mahmoud Saad     | Database Engineer     | 20220356    |
| 5  | Malak Tarek Abdallah        | UI/UX Designer        | 20220274    |
| 6  | Ahmed Mostafa Sayed         | DevOps / Docker       | 20220045    |
| 7  | Sara Hesham Mohamed         | QA / Documentation    | 20220331    |

---

## 🏗 Project Architecture

```
┌──────────────────────┐         HTTP / JSON         ┌──────────────────────┐
│                      │  ◄──────────────────────►   │                      │
│   React + Tailwind   │        Port 5173            │    Flask REST API    │
│      Frontend        │                             │       Backend        │
│                      │    Authorization: Bearer     │                      │
│   (Vite Dev Server)  │  ──────────────────────►    │   (Gunicorn WSGI)   │
│                      │                             │                      │
└──────────────────────┘                             └──────────┬───────────┘
                                                                │
                                                                │ SQLAlchemy ORM
                                                                ▼
                                                     ┌──────────────────────┐
                                                     │      SQLite DB       │
                                                     │    (vigil.db)        │
                                                     │                      │
                                                     │  • User              │
                                                     │  • Target            │
                                                     │  • Log               │
                                                     └──────────────────────┘
```

---

## 🛠 Technology Stack

| Layer      | Technology                           |
|------------|--------------------------------------|
| Frontend   | React 18, Tailwind CSS, Vite         |
| Backend    | Python 3.12, Flask 3.1, SQLAlchemy   |
| Database   | SQLite 3 (file-based relational DB)  |
| Auth       | JWT (PyJWT) with Bearer Tokens       |
| DevOps     | Docker, Docker Compose               |
| Server     | Gunicorn (WSGI Production Server)    |

---

## 🗃 Database Schema (ERD)

The application uses **3 normalized tables** with the following relationships:

| Table    | Columns                                        | Constraints                            |
|----------|------------------------------------------------|----------------------------------------|
| `User`   | `id` PK, `username` UNIQUE, `email` UNIQUE, `password_hash` | Primary entity                |
| `Target` | `id` PK, `name`, `url`, `status`, `user_id` FK | Composite UNIQUE (`user_id`, `url`)    |
| `Log`    | `id` PK, `target_id` FK, `timestamp`, `details`| Cascade delete with Target             |

> **Key Design Decision:** The `url` column is NOT globally unique. A composite unique constraint on `(user_id, url)` ensures the same user cannot track a duplicate URL, while different users are free to monitor the same website independently.

---

## 📡 API Documentation

**Base URL:** `http://localhost:5000/api`

### Authentication Endpoints

| Method | Endpoint          | Auth?  | Description                    | Request Body                                        |
|--------|-------------------|--------|--------------------------------|-----------------------------------------------------|
| POST   | `/api/register`   | ❌ No  | Register a new user            | `{ "username", "email", "password" }`               |
| POST   | `/api/login`      | ❌ No  | Login and receive JWT token    | `{ "email", "password" }`                           |
| POST   | `/api/logout`     | ✅ Yes | Invalidate current JWT token   | —                                                   |

### Target Endpoints

| Method | Endpoint                  | Auth?  | Description                        | Request Body              |
|--------|---------------------------|--------|------------------------------------|---------------------------|
| GET    | `/api/targets`            | ✅ Yes | List all targets for current user  | —                         |
| POST   | `/api/targets`            | ✅ Yes | Add a new monitoring target        | `{ "name", "url" }`      |
| DELETE | `/api/targets/<id>`       | ✅ Yes | Delete a specific target           | —                         |

### Log Endpoints

| Method | Endpoint                      | Auth?  | Description                          |
|--------|-------------------------------|--------|--------------------------------------|
| GET    | `/api/targets/<id>/logs`      | ✅ Yes | Retrieve check history for a target  |

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
<summary><strong>GET /api/targets — 200 OK</strong></summary>

```json
{
  "count": 2,
  "targets": [
    {
      "id": 1,
      "name": "Google",
      "url": "https://google.com",
      "status": "Up",
      "user_id": 1,
      "last_checked": "2026-05-03T17:00:00"
    }
  ]
}
```
</details>

<details>
<summary><strong>GET /api/targets/1/logs — 200 OK</strong></summary>

```json
{
  "target": { "id": 1, "name": "Google", "url": "https://google.com" },
  "count": 5,
  "logs": [
    {
      "id": 10,
      "timestamp": "2026-05-03T17:00:00",
      "details": "Status: Up — 200 OK (142ms)"
    }
  ]
}
```
</details>

---

## 🚀 Getting Started

### Prerequisites

- **Docker** & **Docker Compose** installed ([Get Docker](https://docs.docker.com/get-docker/))
- **Git** for cloning the repository

### Local Development (without Docker)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/vigil-v2.git
cd vigil-v2

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                   # Starts on http://localhost:5000

# 3. Frontend setup (separate terminal)
cd frontend
npm install
npm run dev                     # Starts on http://localhost:5173
```

---

## 🐳 Docker Setup

### Quick Start

```bash
# Build and start all services
docker-compose up --build

# Run in detached (background) mode
docker-compose up --build -d

# Stop all services
docker-compose down

# Stop and remove volumes (reset database)
docker-compose down -v
```

### Services

| Service    | Container Name     | Port  | Description               |
|------------|--------------------|-------|---------------------------|
| `backend`  | `vigil-backend`    | 5000  | Flask REST API (Gunicorn) |
| `frontend` | `vigil-frontend`   | 5173  | React Dev Server (Vite)   |

### Environment Variables

| Variable        | Default                                    | Description              |
|-----------------|--------------------------------------------|--------------------------|
| `SECRET_KEY`    | `vigil-super-secret-key-change-in-production` | JWT signing secret    |
| `DATABASE_URI`  | `sqlite:///vigil.db`                       | SQLAlchemy database URI  |
| `VITE_API_URL`  | `http://localhost:5000/api`                | Frontend API base URL    |

---

## 📁 Project Structure

```
vigil-v2-flask/
├── backend/
│   ├── app.py                  # Flask application (models + routes)
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Backend container image
├── frontend/
│   ├── src/                    # React components & pages
│   ├── package.json            # Node dependencies
│   └── Dockerfile              # Frontend container image
├── docker-compose.yml          # Multi-service orchestration
└── README.md                   # This file
```

---

## 📄 License

This project is developed for academic purposes as part of a university software engineering course. All rights reserved by the team members listed above.

---

<p align="center">
  <strong>Built with ❤️ by the Vigil Team</strong>
</p>