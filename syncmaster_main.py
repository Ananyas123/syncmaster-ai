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
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  input_text TEXT, goals_count INTEGER,
                  tasks_count INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# ── Agent 1: Primary Analysis Agent ───────────────────────────────────────
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
        'deploy': ('Project', 'high'),
        'launch': ('Project', 'critical'),
        'review': ('Professional', 'medium'),
        'debug': ('Project', 'high'),
        'hackathon': ('Project', 'critical'),
        'certification': ('Career', 'high'),
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
    return {
        'summary': summary,
        'goals': identified,
        'complexity': 'Critical' if any(g['priority']=='critical' for g in identified) else ('High' if len(identified) > 2 else 'Medium'),
        'agent': 'PrimaryAgent-v3',
        'categories': categories
    }

# ── Agent 2: Task Breakdown Agent ─────────────────────────────────────────
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
                all_tasks.append({
                    'task': task_name, 'priority': priority, 'deadline': deadline,
                    'category': category, 'status': 'pending', 'id': c.lastrowid
                })
    conn.commit()
    conn.close()
    return {'tasks': all_tasks[:12], 'total_saved': len(all_tasks), 'agent': 'TaskAgent-v3', 'db': 'SQLite'}

# ── Agent 3: Schedule MCP Agent ───────────────────────────────────────────
def schedule_mcp_agent(tasks):
    schedule = {}
    base = datetime.now()
    time_slots = ['08:00','09:30','11:00','13:00','14:30','16:00','18:00','20:00']
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    sorted_tasks = sorted(tasks, key=lambda x: priority_order.get(x['priority'], 3))
    day_names = ['Today', 'Tomorrow', 'Day 3', 'Day 4', 'Day 5']
    durations = [45, 60, 90, 120]
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
            'duration': f"{random.choice(durations)} min",
            'priority': task['priority'],
            'category': task['category'],
        })
    return {
        'schedule': schedule,
        'agent': 'ScheduleMCP-v3',
        'mcp_tool': 'calendar_integration',
        'total_days': len(schedule)
    }

# ── HTML UI ────────────────────────────────────────────────────────────────
HTML = open('templates/index.html').read() if __name__ != '__main__' else None

# ── Routes ─────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    from pathlib import Path
    html = Path('templates/index.html').read_text()
    return html

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
        # Save session
        conn = sqlite3.connect('syncmaster.db')
        c = conn.cursor()
        c.execute('INSERT INTO sessions (input_text, goals_count, tasks_count) VALUES (?,?,?)',
                  (goal[:200], len(analysis['goals']), len(tasks['tasks'])))
        conn.commit()
        conn.close()
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

@app.route('/stats', methods=['GET'])
def get_stats():
    conn = sqlite3.connect('syncmaster.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM tasks')
    total_tasks = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM sessions')
    total_sessions = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM tasks WHERE status="done"')
    done_tasks = c.fetchone()[0]
    conn.close()
    return jsonify({'total_tasks': total_tasks, 'total_sessions': total_sessions, 'done_tasks': done_tasks})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

