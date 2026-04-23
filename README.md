# SyncMaster AI 🤖
### Multi-Agent AI Planning System

> *Transform overwhelming goals into structured, time-bound action plans — powered by three specialized AI agents working in pipeline.*

<br/>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=flat-square&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-Gen_AI_Academy-4285F4?style=flat-square&logo=googlecloud&logoColor=white)
![Status](https://img.shields.io/badge/Status-Live-00d4aa?style=flat-square)

---

## 🧩 The Problem

Students, developers, and professionals constantly face the same challenge — they have multiple goals, deadlines, and priorities colliding at once, but no intelligent system to break them down and schedule them automatically.

SyncMaster solves this with a **multi-agent AI pipeline** that takes a single natural language input and produces a full task breakdown with an optimized 5-day schedule.


## ⚡ How It Works

SyncMaster runs three specialized agents in sequence:

```
User Input → [PrimaryAgent] → [TaskAgent] → [ScheduleMCP] → Dashboard
```

### 🧠 Agent 1 — PrimaryAgent-v3
- Parses natural language input across **18 semantic categories**
- Identifies goals, assigns priority levels (`critical / high / medium / low`)
- Computes complexity score and category classification
- Output: structured goal objects with context

### 📋 Agent 2 — TaskAgent-v3
- Receives goal objects from PrimaryAgent
- Applies **category-specific task templates** (Academic, Project, Career, Professional, etc.)
- Generates concrete, deadline-bound tasks
- **Persists all tasks to SQLite** with auto-incremented IDs

### 📅 Agent 3 — ScheduleMCP-v3
- Receives prioritized task list from TaskAgent
- Uses **MCP calendar_integration tool** to assign time slots
- Builds a **5-day optimized schedule** — critical tasks at peak hours
- Returns structured day-by-day calendar

---

## 🖥️ Features

| Feature | Description |
|---|---|
| **Multi-Module Dashboard** | Tabbed interface: Analysis · Tasks · Schedule |
| **Scrollytelling UI** | Animated "How It Works" with scroll-triggered reveals |
| **Emotional Waterfall Timeline** | 5-phase journey from chaos → clarity |
| **Live Agent Pipeline** | Real-time status bar showing each agent's progress |
| **Task Filtering** | Filter by All / Critical / High / Medium priority |
| **Animated Stats** | Live counters for goals, tasks, days planned |
| **SQLite Persistence** | All tasks saved across sessions |
| **Check-off System** | Mark tasks done directly in the UI |

---

## 🗂️ Project Structure

```
syncmaster-ai/
│
├── syncmaster_main.py      # Flask app + all three AI agents
├── templates/
│   └── index.html          # Full dashboard UI (1,182 lines)
├── requirements.txt        # Python dependencies
├── syncmaster.db           # SQLite database (auto-created)
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/Ananyas123/syncmaster-ai.git
cd syncmaster-ai

# Install dependencies
pip install -r requirements.txt

# Run the app
python syncmaster_main.py
```

Open your browser at `http://localhost:5000`

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Main dashboard UI |
| `POST` | `/process_goal` | Run full agent pipeline |
| `GET` | `/tasks` | Fetch all saved tasks from SQLite |
| `GET` | `/stats` | Session and task statistics |

### Example Request

```bash
curl -X POST http://localhost:5000/process_goal \
  -H "Content-Type: application/json" \
  -d '{"goal": "I have a Networks exam next week and a Java project due Friday"}'
```

### Example Response

```json
{
  "analysis": {
    "summary": "Identified 2 core objectives...",
    "goals": [...],
    "complexity": "High",
    "agent": "PrimaryAgent-v3"
  },
  "tasks": {
    "tasks": [...],
    "total_saved": 8,
    "agent": "TaskAgent-v3",
    "db": "SQLite"
  },
  "schedule": {
    "schedule": {...},
    "total_days": 3,
    "agent": "ScheduleMCP-v3",
    "mcp_tool": "calendar_integration"
  }
}
```

---

## 🗄️ Database Schema

```sql
-- Tasks table
CREATE TABLE tasks (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  goal        TEXT,
  task        TEXT,
  priority    TEXT,   -- critical | high | medium | low
  deadline    TEXT,
  status      TEXT,   -- pending | done
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table
CREATE TABLE sessions (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  input_text  TEXT,
  goals_count INTEGER,
  tasks_count INTEGER,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎯 Supported Goal Categories

| Category | Keywords Detected |
|---|---|
| Academic | exam, test, study, assignment |
| Project | project, deploy, launch, debug, hackathon |
| Professional | meeting, presentation, report, review |
| Career | interview, certification |
| Learning | learn |
| Task | deadline, submit |
| Personal | (fallback for all other inputs) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python · Flask · Flask-CORS |
| Database | SQLite3 (built-in) |
| Frontend | Vanilla HTML · CSS · JavaScript |
| Fonts | Syne · DM Mono · Fraunces (Google Fonts) |
| Deployment | Render.com |
| Architecture | Multi-Agent Pipeline · MCP Tool Pattern |

---

## 📸 UI Architecture

```
┌─────────────────────────────────────────┐
│              HERO SECTION               │  ← Input + Agent activation
├─────────────────────────────────────────┤
│           PIPELINE STATUS BAR           │  ← Live agent progress
├─────────────────────────────────────────┤
│              STATS BAR                  │  ← Goals · Tasks · Days
├─────────────────────────────────────────┤
│         MULTI-MODULE DASHBOARD          │
│  [ Analysis ] [ Tasks ] [ Schedule ]    │  ← Tabbed modules
├─────────────────────────────────────────┤
│        SCROLLYTELLING SECTION           │  ← Animated How It Works
├─────────────────────────────────────────┤
│      WATERFALL EMOTIONAL TIMELINE       │  ← 5-phase user journey
└─────────────────────────────────────────┘
```

---

## 🏆 Built For

**Google Cloud Gen AI Academy — APAC Edition**
Cohort 2 · Hackathon Track
*Top 100 Shortlisted Project*

---

## 👩‍💻 Author

**Ananya Singh**
B.Tech CSE · MPGI, Lucknow
GitHub: [@Ananyas123](https://github.com/Ananyas123)

---

<div align="center">
  <sub>Built with 💙 for the Google Cloud Gen AI Academy APAC Hackathon</sub>
</div>
