from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import json
import random
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# ── Database Setup ─────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect('syncmaster.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  goal TEXT, task TEXT, priority TEXT,
                  deadline TEXT, status TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# ── Mock AI Agents ─────────────────────────────────────────────────────────
def primary_agent_analyze(text):
    keywords = {
        'exam': ('Academic', 'high'),
        'test': ('Academic', 'high'),
        'project': ('Project', 'high'),
        'meeting': ('Professional', 'medium'),
        'assignment': ('Academic', 'medium'),
        'presentation': ('Professional', 'high'),
        'deadline': ('Task', 'high'),
        'learn': ('Learning', 'medium'),
        'study': ('Academic', 'high'),
        'report': ('Professional', 'medium'),
        'interview': ('Career', 'critical'),
        'submit': ('Task', 'high'),
    }
    text_lower = text.lower()
    identified = []
    for kw, (cat, pri) in keywords.items():
        if kw in text_lower:
            words = text_lower.split()
            for i, w in enumerate(words):
                if kw in w:
                    phrase = ' '.join(words[max(0,i-2):min(len(words),i+4)])
                    identified.append({'keyword': kw, 'category': cat, 'priority': pri, 'context': phrase})
                    break
    if not identified:
        identified.append({'keyword': 'general goal', 'category': 'Personal', 'priority': 'medium', 'context': text[:80]})
    summary = f"Identified {len(identified)} core objective(s) from your input. "
    categories = list(set([i['category'] for i in identified]))
    summary += f"Categories: {', '.join(categories)}. "
    high = [i for i in identified if i['priority'] in ['high','critical']]
    if high:
        summary += f"{len(high)} high-priority item(s) require immediate attention."
    return {'summary': summary, 'goals': identified, 'complexity': 'High' if len(identified) > 2 else 'Medium', 'agent': 'PrimaryAgent-v2'}

def task_agent_breakdown(goals, original_text):
    task_templates = {
        'Academic': [
            ('Review lecture notes and past papers', 'high', 2),
            ('Create a study schedule and mind maps', 'high', 1),
            ('Practice problems and mock tests', 'high', 3),
            ('Form or join a study group', 'medium', 4),
            ('Summarize key concepts in flashcards', 'medium', 2),
        ],
        'Project': [
            ('Define project scope and requirements', 'high', 1),
            ('Break project into modules/milestones', 'high', 1),
            ('Set up development environment', 'medium', 1),
            ('Implement core functionality', 'high', 3),
            ('Write tests and documentation', 'medium', 2),
            ('Final review and submission', 'high', 1),
        ],
        'Professional': [
            ('Prepare agenda and materials', 'high', 1),
            ('Research relevant background info', 'medium', 1),
            ('Draft key talking points', 'medium', 1),
            ('Send calendar invites to stakeholders', 'low', 1),
        ],
        'Learning': [
            ('Identify learning resources and materials', 'medium', 1),
            ('Set daily learning targets', 'medium', 1),
            ('Take structured notes', 'medium', 2),
            ('Do hands-on practice exercises', 'high', 2),
        ],
        'Career': [
            ('Research the company and role thoroughly', 'critical', 2),
            ('Prepare answers to common questions', 'high', 2),
            ('Do mock interviews with a friend', 'high', 1),
            ('Prepare questions to ask interviewer', 'medium', 1),
            ('Review and update your resume', 'high', 1),
        ],
        'Personal': [
            ('Break goal into smaller actionable steps', 'medium', 1),
            ('Set a realistic timeline', 'medium', 1),
            ('Identify required resources', 'medium', 1),
            ('Track progress daily', 'low', 1),
        ],
        'Task': [
            ('List all requirements', 'high', 1),
            ('Prioritize by urgency and importance', 'high', 1),
            ('Complete highest priority items first', 'high', 2),
            ('Review and verify completion', 'medium', 1),
        ],
    }
    all_tasks = []
    conn = sqlite3.connect('syncmaster.db')
    c = conn.cursor()
    base_date = datetime.now()
    seen = set()
    for goal in goals:
        category = goal.get('category', 'Personal')
        templates = task_templates.get(category, task_templates['Personal'])
        for task_name, priority, days_offset in templates[:4]:
            if task_name not in seen:
                seen.add(task_name)
                deadline = (base_date + timedelta(days=days_offset)).strftime('%Y-%m-%d')
                c.execute('INSERT INTO tasks (goal, task, priority, deadline, status) VALUES (?,?,?,?,?)',
                         (goal['context'][:100], task_name, priority, deadline, 'pending'))
                all_tasks.append({'task': task_name, 'priority': priority, 'deadline': deadline,
                                 'category': category, 'status': 'pending', 'id': c.lastrowid})
    conn.commit()
    conn.close()
    return {'tasks': all_tasks[:12], 'total_saved': len(all_tasks), 'agent': 'TaskAgent-v2', 'db': 'SQLite'}

def schedule_mcp_agent(tasks):
    schedule = {}
    base = datetime.now()
    time_slots = ['08:00','09:00','10:30','12:00','14:00','15:30','17:00','19:00','20:30']
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    sorted_tasks = sorted(tasks, key=lambda x: priority_order.get(x['priority'], 3))
    day_names = ['Today', 'Tomorrow', 'Day 3', 'Day 4', 'Day 5']
    for i, task in enumerate(sorted_tasks[:10]):
        day_idx = i // 3
        slot_idx = i % len(time_slots)
        day_key = day_names[min(day_idx, 4)]
        date_str = (base + timedelta(days=day_idx)).strftime('%b %d')
        if day_key not in schedule:
            schedule[day_key] = {'date': date_str, 'slots': []}
        schedule[day_key]['slots'].append({
            'time': time_slots[slot_idx],
            'task': task['task'],
            'duration': f"{random.choice([60,90,120])} min",
            'priority': task['priority'],
            'category': task['category'],
        })
    return {'schedule': schedule, 'agent': 'ScheduleMCP-v2', 'mcp_tool': 'calendar_integration', 'total_days': len(schedule)}

# ── HTML UI ────────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>SyncMaster — Multi-Agent AI Planner</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<style>
:root {
  --bg: #0d1117; --surface: #161b22; --card: #1c2128; --border: #30363d;
  --blue: #58a6ff; --green: #3fb950; --purple: #bc8cff; --orange: #e3b341;
  --red: #ff7b72; --text: #e6edf3; --muted: #7d8590; --accent: #1f6feb;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; min-height: 100vh; }

/* Header */
.header {
  background: linear-gradient(135deg, #0d1117 0%, #1a1f2e 100%);
  border-bottom: 1px solid var(--border);
  padding: 20px 40px;
  display: flex; align-items: center; gap: 16px;
}
.logo {
  width: 44px; height: 44px; background: linear-gradient(135deg, var(--blue), var(--purple));
  border-radius: 12px; display: flex; align-items: center; justify-content: center;
  font-size: 22px;
}
.header-text h1 { font-size: 22px; font-weight: 800; background: linear-gradient(90deg, var(--blue), var(--purple)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header-text p { font-size: 12px; color: var(--muted); margin-top: 2px; }
.agent-badges { margin-left: auto; display: flex; gap: 8px; }
.badge { padding: 4px 10px; border-radius: 20px; font-size: 11px; font-family: 'JetBrains Mono', monospace; border: 1px solid; }
.badge-blue { border-color: var(--blue); color: var(--blue); background: rgba(88,166,255,0.1); }
.badge-green { border-color: var(--green); color: var(--green); background: rgba(63,185,80,0.1); }
.badge-purple { border-color: var(--purple); color: var(--purple); background: rgba(188,140,255,0.1); }

/* Main */
.container { max-width: 1400px; margin: 0 auto; padding: 32px 40px; }

/* Input Section */
.input-section { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 28px; margin-bottom: 32px; }
.input-label { font-size: 13px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px; }
.input-wrapper { position: relative; }
textarea {
  width: 100%; background: var(--bg); border: 1px solid var(--border); border-radius: 12px;
  padding: 16px 20px; color: var(--text); font-family: 'Inter', sans-serif; font-size: 15px;
  resize: none; outline: none; transition: border-color 0.2s; min-height: 100px;
}
textarea:focus { border-color: var(--blue); }
textarea::placeholder { color: var(--muted); }
.btn-row { display: flex; gap: 12px; margin-top: 16px; align-items: center; }
.btn-primary {
  padding: 12px 28px; background: linear-gradient(135deg, var(--accent), #388bfd);
  color: white; border: none; border-radius: 10px; font-family: 'Inter', sans-serif;
  font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; gap: 8px;
}
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(31,111,235,0.4); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.btn-secondary {
  padding: 12px 20px; background: transparent; color: var(--muted); border: 1px solid var(--border);
  border-radius: 10px; font-family: 'Inter', sans-serif; font-size: 14px; cursor: pointer; transition: all 0.2s;
}
.btn-secondary:hover { border-color: var(--text); color: var(--text); }
.examples { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.example-chip {
  padding: 5px 12px; background: rgba(88,166,255,0.08); border: 1px solid rgba(88,166,255,0.2);
  border-radius: 20px; font-size: 12px; color: var(--blue); cursor: pointer; transition: all 0.2s;
}
.example-chip:hover { background: rgba(88,166,255,0.15); }

/* Agent Pipeline */
.pipeline { display: flex; gap: 12px; margin-bottom: 24px; align-items: center; }
.pipeline-step {
  flex: 1; background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 12px 16px; display: flex; align-items: center; gap: 10px; transition: all 0.3s;
}
.pipeline-step.active { border-color: var(--blue); background: rgba(88,166,255,0.05); }
.pipeline-step.done { border-color: var(--green); background: rgba(63,185,80,0.05); }
.step-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
.step-icon-blue { background: rgba(88,166,255,0.15); }
.step-icon-green { background: rgba(63,185,80,0.15); }
.step-icon-purple { background: rgba(188,140,255,0.15); }
.step-info { flex: 1; }
.step-name { font-size: 12px; font-weight: 600; }
.step-status { font-size: 11px; color: var(--muted); margin-top: 2px; font-family: 'JetBrains Mono', monospace; }
.pipeline-arrow { color: var(--muted); font-size: 18px; flex-shrink: 0; }

/* Spinner */
.spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Results Grid */
.results-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.result-card { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; }
.card-header { padding: 18px 20px 14px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 10px; }
.card-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.card-title { font-size: 14px; font-weight: 700; }
.card-subtitle { font-size: 11px; color: var(--muted); margin-top: 2px; font-family: 'JetBrains Mono', monospace; }
.card-body { padding: 20px; max-height: 520px; overflow-y: auto; }
.card-body::-webkit-scrollbar { width: 4px; }
.card-body::-webkit-scrollbar-track { background: transparent; }
.card-body::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* Analysis Card */
.summary-box { background: rgba(88,166,255,0.06); border: 1px solid rgba(88,166,255,0.15); border-radius: 10px; padding: 14px; margin-bottom: 16px; font-size: 13px; line-height: 1.6; color: #cdd9e5; }
.goal-item { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; }
.goal-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.goal-category { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 12px; }
.cat-academic { background: rgba(88,166,255,0.15); color: var(--blue); }
.cat-project { background: rgba(63,185,80,0.15); color: var(--green); }
.cat-professional { background: rgba(188,140,255,0.15); color: var(--purple); }
.cat-career { background: rgba(255,123,114,0.15); color: var(--red); }
.cat-learning { background: rgba(227,179,65,0.15); color: var(--orange); }
.cat-personal { background: rgba(125,133,144,0.15); color: var(--muted); }
.cat-task { background: rgba(88,166,255,0.15); color: var(--blue); }
.priority-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.p-critical { background: var(--red); }
.p-high { background: var(--orange); }
.p-medium { background: var(--blue); }
.p-low { background: var(--muted); }
.goal-context { font-size: 12px; color: var(--muted); font-style: italic; }
.complexity-badge { display: inline-flex; align-items: center; gap: 6px; background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; font-size: 12px; margin-top: 8px; }

/* Tasks Card */
.task-item { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; display: flex; align-items: flex-start; gap: 10px; cursor: pointer; transition: all 0.2s; }
.task-item:hover { border-color: var(--blue); transform: translateX(3px); }
.task-check { width: 18px; height: 18px; border-radius: 5px; border: 2px solid var(--border); flex-shrink: 0; margin-top: 1px; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.task-item.done .task-check { background: var(--green); border-color: var(--green); }
.task-item.done .task-name { text-decoration: line-through; color: var(--muted); }
.task-info { flex: 1; }
.task-name { font-size: 13px; font-weight: 500; margin-bottom: 5px; }
.task-meta { display: flex; gap: 8px; align-items: center; }
.task-deadline { font-size: 11px; color: var(--muted); font-family: 'JetBrains Mono', monospace; }
.db-badge { font-size: 10px; background: rgba(63,185,80,0.1); color: var(--green); border: 1px solid rgba(63,185,80,0.2); padding: 1px 6px; border-radius: 8px; font-family: 'JetBrains Mono', monospace; }

/* Schedule Card */
.day-block { margin-bottom: 18px; }
.day-header { font-size: 12px; font-weight: 700; color: var(--purple); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
.day-date { font-weight: 400; color: var(--muted); font-family: 'JetBrains Mono', monospace; text-transform: none; letter-spacing: 0; }
.slot-item { display: flex; gap: 10px; align-items: flex-start; padding: 10px 12px; background: var(--card); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 6px; border-left: 3px solid; }
.slot-time { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--muted); flex-shrink: 0; padding-top: 1px; width: 46px; }
.slot-info { flex: 1; }
.slot-task { font-size: 13px; font-weight: 500; margin-bottom: 3px; }
.slot-duration { font-size: 11px; color: var(--muted); }
.mcp-indicator { font-size: 10px; background: rgba(188,140,255,0.1); color: var(--purple); border: 1px solid rgba(188,140,255,0.2); padding: 2px 7px; border-radius: 8px; font-family: 'JetBrains Mono', monospace; margin-top: 4px; display: inline-block; }

/* Priority colors for slots */
.slot-critical { border-left-color: var(--red); }
.slot-high { border-left-color: var(--orange); }
.slot-medium { border-left-color: var(--blue); }
.slot-low { border-left-color: var(--muted); }

/* Empty state */
.empty-state { text-align: center; padding: 60px 20px; color: var(--muted); }
.empty-icon { font-size: 48px; margin-bottom: 12px; opacity: 0.5; }
.empty-text { font-size: 14px; }

/* Stats bar */
.stats-bar { display: flex; gap: 16px; margin-bottom: 24px; }
.stat-item { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px 18px; flex: 1; }
.stat-value { font-size: 24px; font-weight: 800; font-family: 'JetBrains Mono', monospace; }
.stat-label { font-size: 11px; color: var(--muted); margin-top: 3px; }

@media (max-width: 900px) {
  .results-grid { grid-template-columns: 1fr; }
  .pipeline { flex-direction: column; }
  .pipeline-arrow { transform: rotate(90deg); }
  .container { padding: 20px; }
  .header { padding: 16px 20px; }
  .agent-badges { display: none; }
}
</style>
</head>
<body>

<div class="header">
  <div class="logo">🤖</div>
  <div class="header-text">
    <h1>SyncMaster</h1>
    <p>Multi-Agent AI Planning System</p>
  </div>
  <div class="agent-badges">
    <span class="badge badge-blue">PrimaryAgent-v2</span>
    <span class="badge badge-green">TaskAgent-v2</span>
    <span class="badge badge-purple">ScheduleMCP-v2</span>
  </div>
</div>

<div class="container">

  <!-- Input Section -->
  <div class="input-section">
    <div class="input-label">// Enter your goal or challenge</div>
    <div class="input-wrapper">
      <textarea id="goalInput" rows="3" placeholder="e.g. I have a Computer Networks exam next week and a Java project due Friday. I also have a team meeting tomorrow."></textarea>
    </div>
    <div class="btn-row">
      <button class="btn-primary" id="analyzeBtn" onclick="processGoal()">
        <span id="btnIcon">⚡</span>
        <span id="btnText">Activate Agents</span>
      </button>
      <button class="btn-secondary" onclick="clearAll()">Clear</button>
      <span style="font-size:12px;color:var(--muted);margin-left:8px;">Try an example:</span>
    </div>
    <div class="examples">
      <span class="example-chip" onclick="setExample(this)">Computer Networks exam + Java project due Friday</span>
      <span class="example-chip" onclick="setExample(this)">Job interview at Google next Tuesday, need to prepare</span>
      <span class="example-chip" onclick="setExample(this)">ML assignment submission + team presentation this week</span>
      <span class="example-chip" onclick="setExample(this)">Study for 3 finals, submit research report, gym daily</span>
    </div>
  </div>

  <!-- Agent Pipeline -->
  <div class="pipeline" id="pipeline">
    <div class="pipeline-step" id="step1">
      <div class="step-icon step-icon-blue">🧠</div>
      <div class="step-info">
        <div class="step-name" style="color:var(--blue)">Primary Agent</div>
        <div class="step-status" id="status1">Waiting for input...</div>
      </div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step" id="step2">
      <div class="step-icon step-icon-green">📋</div>
      <div class="step-info">
        <div class="step-name" style="color:var(--green)">Task Agent</div>
        <div class="step-status" id="status2">Waiting...</div>
      </div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step" id="step3">
      <div class="step-icon step-icon-purple">📅</div>
      <div class="step-info">
        <div class="step-name" style="color:var(--purple)">Schedule MCP</div>
        <div class="step-status" id="status3">Waiting...</div>
      </div>
    </div>
  </div>

  <!-- Stats Bar (hidden initially) -->
  <div class="stats-bar" id="statsBar" style="display:none">
    <div class="stat-item">
      <div class="stat-value" id="statGoals" style="color:var(--blue)">0</div>
      <div class="stat-label">Goals Identified</div>
    </div>
    <div class="stat-item">
      <div class="stat-value" id="statTasks" style="color:var(--green)">0</div>
      <div class="stat-label">Tasks Created</div>
    </div>
    <div class="stat-item">
      <div class="stat-value" id="statDays" style="color:var(--purple)">0</div>
      <div class="stat-label">Days Scheduled</div>
    </div>
    <div class="stat-item">
      <div class="stat-value" style="color:var(--orange)">SQLite</div>
      <div class="stat-label">Database Active</div>
    </div>
  </div>

  <!-- Results Grid -->
  <div class="results-grid">

    <!-- Analysis Card -->
    <div class="result-card">
      <div class="card-header">
        <div class="card-icon" style="background:rgba(88,166,255,0.15)">🧠</div>
        <div>
          <div class="card-title">Analysis</div>
          <div class="card-subtitle">primary_agent.analyze()</div>
        </div>
      </div>
      <div class="card-body" id="analysisCard">
        <div class="empty-state">
          <div class="empty-icon">🧠</div>
          <div class="empty-text">Primary Agent is standing by</div>
        </div>
      </div>
    </div>

    <!-- Tasks Card -->
    <div class="result-card">
      <div class="card-header">
        <div class="card-icon" style="background:rgba(63,185,80,0.15)">📋</div>
        <div>
          <div class="card-title">Task List</div>
          <div class="card-subtitle">task_agent.breakdown() → SQLite</div>
        </div>
      </div>
      <div class="card-body" id="tasksCard">
        <div class="empty-state">
          <div class="empty-icon">📋</div>
          <div class="empty-text">Task Agent is standing by</div>
        </div>
      </div>
    </div>

    <!-- Schedule Card -->
    <div class="result-card">
      <div class="card-header">
        <div class="card-icon" style="background:rgba(188,140,255,0.15)">📅</div>
        <div>
          <div class="card-title">Schedule</div>
          <div class="card-subtitle">mcp_agent.calendar_integration()</div>
        </div>
      </div>
      <div class="card-body" id="scheduleCard">
        <div class="empty-state">
          <div class="empty-icon">📅</div>
          <div class="empty-text">Schedule MCP Agent is standing by</div>
        </div>
      </div>
    </div>

  </div>
</div>

<script>
function setExample(el) {
  document.getElementById('goalInput').value = el.textContent;
}

function clearAll() {
  document.getElementById('goalInput').value = '';
  document.getElementById('analysisCard').innerHTML = '<div class="empty-state"><div class="empty-icon">🧠</div><div class="empty-text">Primary Agent is standing by</div></div>';
  document.getElementById('tasksCard').innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-text">Task Agent is standing by</div></div>';
  document.getElementById('scheduleCard').innerHTML = '<div class="empty-state"><div class="empty-icon">📅</div><div class="empty-text">Schedule MCP Agent is standing by</div></div>';
  document.getElementById('statsBar').style.display = 'none';
  resetPipeline();
}

function resetPipeline() {
  ['step1','step2','step3'].forEach(id => {
    document.getElementById(id).className = 'pipeline-step';
  });
  document.getElementById('status1').textContent = 'Waiting for input...';
  document.getElementById('status2').textContent = 'Waiting...';
  document.getElementById('status3').textContent = 'Waiting...';
}

function setStep(step, state, msg) {
  const el = document.getElementById('step' + step);
  el.className = 'pipeline-step ' + state;
  document.getElementById('status' + step).textContent = msg;
}

function getPriorityColor(p) {
  return {critical:'var(--red)',high:'var(--orange)',medium:'var(--blue)',low:'var(--muted)'}[p] || 'var(--muted)';
}

function getCatClass(cat) {
  const map = {Academic:'cat-academic',Project:'cat-project',Professional:'cat-professional',Career:'cat-career',Learning:'cat-learning',Personal:'cat-personal',Task:'cat-task'};
  return map[cat] || 'cat-personal';
}

function renderAnalysis(data) {
  let html = `<div class="summary-box">${data.summary}</div>`;
  data.goals.forEach(g => {
    html += `<div class="goal-item">
      <div class="goal-header">
        <span class="goal-category ${getCatClass(g.category)}">${g.category}</span>
        <span class="priority-dot p-${g.priority}" title="${g.priority}"></span>
        <span style="font-size:11px;color:var(--muted);text-transform:capitalize">${g.priority}</span>
      </div>
      <div class="goal-context">"...${g.context}..."</div>
    </div>`;
  });
  html += `<div class="complexity-badge">
    <span style="color:var(--muted)">Complexity:</span>
    <span style="color:var(--orange);font-weight:600">${data.complexity}</span>
    <span style="color:var(--border)">|</span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted)">${data.agent}</span>
  </div>`;
  document.getElementById('analysisCard').innerHTML = html;
}

function renderTasks(data) {
  let html = `<div style="font-size:11px;color:var(--muted);margin-bottom:12px;font-family:'JetBrains Mono',monospace;">
    ${data.total_saved} tasks → ${data.db} ✓
  </div>`;
  data.tasks.forEach((t, i) => {
    html += `<div class="task-item" id="task_${i}" onclick="toggleTask(${i})">
      <div class="task-check" id="check_${i}"></div>
      <div class="task-info">
        <div class="task-name">${t.task}</div>
        <div class="task-meta">
          <span class="priority-dot p-${t.priority}"></span>
          <span class="task-deadline">📅 ${t.deadline}</span>
          <span class="db-badge">DB #${t.id}</span>
        </div>
      </div>
    </div>`;
  });
  document.getElementById('tasksCard').innerHTML = html;
}

function toggleTask(i) {
  const el = document.getElementById('task_' + i);
  const check = document.getElementById('check_' + i);
  el.classList.toggle('done');
  check.innerHTML = el.classList.contains('done') ? '✓' : '';
  check.style.color = 'white';
  check.style.fontSize = '11px';
  check.style.fontWeight = '700';
}

function renderSchedule(data) {
  let html = `<div style="font-size:11px;color:var(--muted);margin-bottom:14px;font-family:'JetBrains Mono',monospace;">
    mcp_tool: ${data.mcp_tool} ✓ | ${data.total_days} days planned
  </div>`;
  for (const [day, info] of Object.entries(data.schedule)) {
    html += `<div class="day-block">
      <div class="day-header">${day} <span class="day-date">${info.date}</span></div>`;
    info.slots.forEach(slot => {
      html += `<div class="slot-item slot-${slot.priority}">
        <div class="slot-time">${slot.time}</div>
        <div class="slot-info">
          <div class="slot-task">${slot.task}</div>
          <div class="slot-duration">⏱ ${slot.duration}</div>
          <span class="mcp-indicator">MCP:calendar</span>
        </div>
      </div>`;
    });
    html += `</div>`;
  }
  document.getElementById('scheduleCard').innerHTML = html;
}

async function processGoal() {
  const goal = document.getElementById('goalInput').value.trim();
  if (!goal) { alert('Please enter a goal first!'); return; }

  const btn = document.getElementById('analyzeBtn');
  btn.disabled = true;
  document.getElementById('btnIcon').innerHTML = '<div class="spinner"></div>';
  document.getElementById('btnText').textContent = 'Agents thinking...';

  resetPipeline();
  setStep(1, 'active', 'Analyzing goals...');

  try {
    const res = await fetch('/process_goal', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({goal})
    });
    const data = await res.json();

    if (data.error) throw new Error(data.error);

    // Animate pipeline
    setStep(1, 'done', `✓ ${data.analysis.goals.length} goals found`);
    await new Promise(r => setTimeout(r, 400));
    setStep(2, 'active', 'Breaking down tasks...');
    await new Promise(r => setTimeout(r, 600));
    setStep(2, 'done', `✓ ${data.tasks.tasks.length} tasks → SQLite`);
    await new Promise(r => setTimeout(r, 400));
    setStep(3, 'active', 'Building schedule...');
    await new Promise(r => setTimeout(r, 500));
    setStep(3, 'done', `✓ ${data.schedule.total_days} days planned`);

    // Render cards
    renderAnalysis(data.analysis);
    renderTasks(data.tasks);
    renderSchedule(data.schedule);

    // Show stats
    document.getElementById('statGoals').textContent = data.analysis.goals.length;
    document.getElementById('statTasks').textContent = data.tasks.tasks.length;
    document.getElementById('statDays').textContent = data.schedule.total_days;
    document.getElementById('statsBar').style.display = 'flex';

  } catch (err) {
    alert('Error: ' + err.message);
    resetPipeline();
  } finally {
    btn.disabled = false;
    document.getElementById('btnIcon').textContent = '⚡';
    document.getElementById('btnText').textContent = 'Activate Agents';
  }
}
</script>
</body>
</html>"""

# ── Routes ─────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/process_goal', methods=['POST'])
def process_goal():
    try:
        data = request.get_json()
        goal = data.get('goal', '').strip()
        if not goal:
            return jsonify({'error': 'No goal provided'}), 400
        analysis = primary_agent_analyze(goal)
        tasks = task_agent_breakdown(analysis['goals'], goal)
        schedule = schedule_mcp_agent(tasks['tasks'])
        return jsonify({'analysis': analysis, 'tasks': tasks, 'schedule': schedule, 'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tasks', methods=['GET'])
def get_tasks():
    conn = sqlite3.connect('syncmaster.db')
    c = conn.cursor()
    c.execute('SELECT * FROM tasks ORDER BY created_at DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    return jsonify([{'id':r[0],'goal':r[1],'task':r[2],'priority':r[3],'deadline':r[4],'status':r[5]} for r in rows])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
