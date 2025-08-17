# app.py - Elyx Member Journey Visualization
# To run:
# pip install flask plotly
# python app.py

from flask import Flask, render_template_string, request, redirect, url_for, session, g
import sqlite3
import json
from datetime import datetime, timedelta
import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder
import random
from jinja2 import DictLoader
import csv

app = Flask(__name__)
app.secret_key = 'elyx_hackathon_2025'
app.config['DATABASE'] = 'elyx.db'
app.jinja_env.globals.update(datetime=datetime)

# ===================================================================
# DATA IMPORT INSTRUCTIONS:
#
# To load your 8-month dataset:
# 1. Prepare your data in CSV format with columns matching the tables:
#    - communications: member_id,date,sender,message,category
#    - interventions: member_id,date,type,category,description,reason,outcome,staff_member,duration_minutes
#    - staff_activity: staff_name,role,date,activity_type,duration_minutes,member_id
#
# 2. Either:
#    a) Replace the sample data lists in load_custom_data() with your actual data tuples, or
#    b) Uncomment the CSV import code and point to your CSV files
#
# 3. The system will automatically handle larger datasets in visualizations
# ===================================================================

def load_custom_data():
    """Load an extended 8-month dataset into the database"""
    db = get_db()
    cursor = db.cursor()
    
    
    # Sample data structure - REPLACE THIS WITH YOUR ACTUAL 8-MONTH DATA
    # Each list contains tuples matching the table schema
    
    # 1. Communications data (8 months of messages)
        # Add 100+ more messages following this pattern
        # Pro tip: Generate this from a CSV using:
    with open('communications.csv') as f:
        communications_data = [tuple(row) for row in csv.reader(f)]
    
    
    # 2. Interventions data (medications, therapies, etc.)
    with open('interventions.csv') as f:
        interventions_data = [tuple(row) for row in csv.reader(f)]
    
    # 3. Staff activity logs
    with open('staff_activity.csv') as f:
        staff_activity_data = [tuple(row) for row in csv.reader(f)]
   
   
    # Bulk insert the data
    if communications_data:
        cursor.executemany('''
            INSERT INTO communications 
            (member_id, date, sender, message, category)
            VALUES (?, ?, ?, ?, ?)
        ''', communications_data)
    
    if interventions_data:
        cursor.executemany('''
            INSERT INTO interventions 
            (member_id, date, type, category, description, reason, outcome, staff_member, duration_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', interventions_data)
    
    if staff_activity_data:
        cursor.executemany('''
            INSERT INTO staff_activity 
            (staff_name, role, date, activity_type, duration_minutes, member_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', staff_activity_data)
    
    db.commit()
    

# Database setup
def get_db():
    db = getattr(g, '_database', None)
    db = g._database = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS member_profiles (
                member_id INTEGER PRIMARY KEY,
                dob TEXT,
                gender TEXT,
                location TEXT,
                occupation TEXT,
                health_goals TEXT,
                chronic_condition TEXT,
                FOREIGN KEY (member_id) REFERENCES members (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interventions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                reason TEXT NOT NULL,
                outcome TEXT,
                staff_member TEXT,
                duration_minutes INTEGER,
                FOREIGN KEY (member_id) REFERENCES members (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS communications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                category TEXT NOT NULL,
                FOREIGN KEY (member_id) REFERENCES members (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_name TEXT NOT NULL,
                role TEXT NOT NULL,
                date TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                member_id INTEGER,
                FOREIGN KEY (member_id) REFERENCES members (id)
            )
        ''')
        
        # Seed initial data if tables are empty
        if cursor.execute('SELECT COUNT(*) FROM members').fetchone()[0] == 0:
            load_custom_data()
            # Add sample members
            cursor.executemany('''
                INSERT INTO members (username, password, full_name, role) 
                VALUES (?, ?, ?, ?)
            ''', [
                ('rohan', 'password123', 'Rohan Patel', 'member'),
                ('ruby', 'password123', 'Ruby', 'staff'),
                ('drwarren', 'password123', 'Dr. Warren', 'staff'),
                ('advik', 'password123', 'Advik', 'staff'),
                ('carla', 'password123', 'Carla', 'staff'),
                ('rachel', 'password123', 'Rachel', 'staff'),
                ('neel', 'password123', 'Neel', 'staff')
            ])
        

            # Add member profile for Rohan
            cursor.execute('''
                INSERT INTO member_profiles (
                    member_id, dob, gender, location, occupation, 
                    health_goals, chronic_condition
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                1, '1979-03-12', 'Male', 'Singapore', 
                'Regional Head of Sales for a FinTech company',
                json.dumps([
                    "Reduce risk of heart disease by maintaining healthy cholesterol and blood pressure levels by December 2026",
                    "Enhance cognitive function and focus for sustained mental performance by June 2026",
                    "Implement annual full-body health screenings starting November 2025"
                ]),
                "High blood pressure"
            ))
            
            # Add sample interventions
            interventions = [
                (1, '2025-01-15', 'Diagnostic', 'Blood Test', 'Initial blood panel', 
                 'Baseline health assessment', 'Pending', 'Dr. Warren', 30),
                (1, '2025-01-20', 'Therapy', 'Physical', 'Initial physio assessment', 
                 'Address back pain from travel', 'Improved mobility', 'Rachel', 60),
                (1, '2025-02-10', 'Medication', 'Supplement', 'Magnesium Threonate', 
                 'Improve sleep quality based on Whoop data', 'Sleep latency reduced', 'Carla', 15),
                (1, '2025-03-05', 'Diagnostic', 'Wearable', 'Whoop strap deployment', 
                 'Track HRV and recovery metrics', 'Data collection started', 'Advik', 20),
                (1, '2025-04-15', 'Exercise', 'Cardio', 'Zone 2 protocol adjustment', 
                 'Improve aerobic capacity', 'Increased duration to 30 mins', 'Advik', 45),
                (1, '2025-05-02', 'Treatment', 'IV Therapy', 'Vitamin C and Zinc IV', 
                 'Boost immune system during illness', 'Faster recovery observed', 'Dr. Warren', 90),
                (1, '2025-06-10', 'Nutrition', 'Diet', 'Time-Restricted Eating', 
                 'Improve metabolic health', 'Reduced glucose spikes', 'Carla', 30),
                (1, '2025-07-15', 'Diagnostic', 'Blood Test', 'Advanced lipid panel', 
                 'Monitor ApoB levels', 'ApoB reduced by 15%', 'Dr. Warren', 30),
                (1, '2025-08-20', 'Exercise', 'Strength', 'Deadlift program', 
                 'Improve structural health', 'Increased strength', 'Rachel', 60)
            ]
            
            cursor.executemany('''
                INSERT INTO interventions (
                    member_id, date, type, category, description, 
                    reason, outcome, staff_member, duration_minutes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', interventions)
            

            # Add sample communications
            communications = []
            base_date = datetime(2025, 1, 15)
            staff_members = ['Ruby', 'Dr. Warren', 'Advik', 'Carla', 'Rachel', 'Neel']
            categories = ['General Query', 'Test Results', 'Plan Update', 'Follow-up', 'Weekly Report']
            
            for i in range(100):
                date = (base_date + timedelta(days=i//5)).strftime('%Y-%m-%d')
                if i % 5 == 0:
                    sender = 'Rohan Patel'
                    message = random.choice([
                        "My Garmin is logging high intensity minutes, even on rest days. What's going on?",
                        "I'm traveling next week - any recommendations for healthy restaurants?",
                        "I'm not sleeping well. Any suggestions?",
                        "The new supplement is causing some stomach discomfort.",
                        "Can we review my latest blood test results?",
                        "I need to adjust my workout schedule due to travel."
                    ])
                else:
                    sender = random.choice(staff_members)
                    message = random.choice([
                        f"Based on your data, I recommend {random.choice(['increasing', 'decreasing'])} your {random.choice(['exercise intensity', 'supplement dosage', 'protein intake'])}.",
                        "Let's schedule a follow-up to discuss your progress.",
                        "Your recent test results show improvement in several markers.",
                        "I've updated your plan based on your feedback.",
                        "Here's a detailed analysis of your current health metrics."
                    ])
                
                communications.append((
                    1, date, sender, message, random.choice(categories)
                ))
            
            cursor.executemany('''
                INSERT INTO communications (
                    member_id, date, sender, message, category
                ) VALUES (?, ?, ?, ?, ?)
            ''', communications)
            
            # Add staff activity
            staff_activity = []
            roles = {
                'Ruby': 'Concierge',
                'Dr. Warren': 'Medical Strategist',
                'Advik': 'Performance Scientist',
                'Carla': 'Nutritionist',
                'Rachel': 'PT/Physiotherapist',
                'Neel': 'Concierge Lead'
            }
            
            for i in range(200):
                staff = random.choice(list(roles.keys()))
                date = (base_date + timedelta(days=i//3)).strftime('%Y-%m-%d')
                activity = random.choice(['Consultation', 'Analysis', 'Planning', 'Follow-up', 'Research'])
                duration = random.choice([15, 30, 45, 60, 90])
                member_id = 1 if random.random() > 0.3 else None
                
                staff_activity.append((
                    staff, roles[staff], date, activity, duration, member_id
                ))
            
            cursor.executemany('''
                INSERT INTO staff_activity (
                    staff_name, role, date, activity_type, duration_minutes, member_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', staff_activity)
            
            db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Helper functions
def get_member_profile(member_id):
    db = get_db()
    profile = db.execute('''
        SELECT * FROM member_profiles WHERE member_id = ?
    ''', (member_id,)).fetchone()
    
    profile = dict(profile)
    profile['health_goals'] = json.loads(profile['health_goals'])
    db.close()
    return profile
    

def get_interventions(member_id, limit=None):
    """Get interventions with optional filtering"""
    db = get_db()
    query = '''
        SELECT * FROM interventions 
        WHERE member_id = ?
        ORDER BY date DESC
    '''
    params = (member_id,)
    
    if limit:
        query += ' LIMIT ?'
        params = (member_id, limit)
        
    interventions = db.execute(query, params).fetchall()
    db.close()
    return interventions

def get_communications(member_id = None, limit=900):
    db = get_db()
    if member_id:
        rows = db.execute("""
        SELECT sender, message, date, category 
        FROM communications
        WHERE member_id = ?
        ORDER BY date DESC
        LIMIT ?
    """, (member_id, limit)).fetchall()
    else:
        rows = db.execute("""
            SELECT sender, message, date, category 
            FROM communications 
            ORDER BY date DESC 
            LIMIT ?;
        """, (limit,)).fetchall()
    

    return [dict(row) for row in rows]

def get_staff_metrics():
    db = get_db()
    metrics = db.execute('''
        SELECT 
            staff_name,
            role,
            SUM(duration_minutes) as total_minutes,
            COUNT(*) as activity_count
        FROM staff_activity
        GROUP BY staff_name
        ORDER BY total_minutes DESC
    ''').fetchall()
    db.close()
    return metrics

def get_staff_hours_by_month():
    db = get_db()
    metrices = db.execute('''
        SELECT 
            strftime('%Y-%m', date) as month,
            staff_name,
            role,
            SUM(duration_minutes)/60.0 as total_hours
        FROM staff_activity
        GROUP BY month, staff_name
        ORDER BY month, staff_name
    ''').fetchall()
    return metrices

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('''
            SELECT * FROM members WHERE username = ?
        ''', (username,)).fetchone()
        
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user[4]
            return redirect(url_for('dashboard'))
        
        return render_template_string('''
            {% extends 'base.html' %}
            {% block content %}
            <div class="alert alert-danger">Invalid credentials. Please try again.</div>
            <form method="post">
                <div class="mb-3">
                    <label for="username" class="form-label">Username</label>
                    <input type="text" class="form-control" id="username" name="username" required>
                </div>
                <div class="mb-3">
                    <label for="password" class="form-label">Password</label>
                    <input type="password" class="form-control" id="password" name="password" required>
                </div>
                <button type="submit" class="btn btn-primary">Login</button>
            </form>
            {% endblock %}
        ''')
    
    return render_template_string('''
        {% extends 'base.html' %}
        {% block content %}
        <h2 class="mb-4">Login to Elyx Member Portal</h2>
        <form method="post">
            <div class="mb-3">
                <label for="username" class="form-label">Username</label>
                <input type="text" class="form-control" id="username" name="username" required>
            </div>
            <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input type="password" class="form-control" id="password" name="password" required>
            </div>
            <button type="submit" class="btn btn-primary">Login</button>
        </form>
        <p class="mt-3">Demo credentials: rohan/password123</p>
        {% endblock %}
    ''')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    member_id = session['user_id']
    profile = get_member_profile(member_id)
    interventions = get_interventions(member_id)
    communications = get_communications(member_id, limit=900)
    staff_metrics = get_staff_metrics()
    staff_hours = get_staff_hours_by_month()
    
    # Prepare data for charts
    # Timeline chart data

    timeline_data = {}

    for intervention in interventions:
        raw_date = intervention['date']

    # Try multiple date formats
        date = None
        for fmt in ("%m/%d/%y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
               date = datetime.strptime(raw_date, fmt)
               break
            except ValueError:
               continue

        if not date:
           print(f"Skipping invalid date: {raw_date}")
           continue

        if date not in timeline_data:
           timeline_data[date] = []
        timeline_data[date].append(intervention)

# ✅ now all keys are datetime objects
    timeline_dates = sorted(timeline_data.keys())

    timeline_categories = {}
    for date in timeline_dates:
        for intervention in timeline_data[date]:
            category = intervention['category']
            if category not in timeline_categories:
               timeline_categories[category] = []
            timeline_categories[category].append((date, intervention['description']))


# Create Plotly timeline figure
    timeline_fig = go.Figure()

    colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3']
    for i, (category, events) in enumerate(timeline_categories.items()):
       dates = [e[0] for e in events]
       texts = [e[1] for e in events]
       timeline_fig.add_trace(go.Scatter(
        x=dates,
        y=[category] * len(dates),
        text=texts,
        mode='markers+text',
        textposition="top center",
        name=category,
        marker=dict(size=12, color=colors[i % len(colors)]),
        hovertemplate="Date: %{x|%b %d, %Y}<br>Category: %{y}<br>%{text}<extra></extra>"
    ))

    timeline_fig.update_layout(
    title='Member Journey Timeline',
    xaxis=dict(title='Date', tickformat="%b %d, %Y"),
    yaxis=dict(title='Intervention Category'),
    showlegend=True,
    height=500
)
    
    timeline_json = json.dumps(timeline_fig, cls=PlotlyJSONEncoder)
    
    # Staff hours by month chart
    staff_names = list(set(m['staff_name'] for m in staff_hours  if m['staff_name'] is not None))
    months = sorted(list(set(m['month'] for m in staff_hours if m['month'] is not None )))
    
    staff_hours_fig = go.Figure()
    
    for i, staff in enumerate(staff_names):
        staff_data = [m for m in staff_hours if m['staff_name'] == staff]
        hours = [m['total_hours'] for m in staff_data]
        staff_hours_fig.add_trace(go.Bar(
            x=months,
            y=hours,
            name=staff,
            marker_color=colors[i % len(colors)]
        ))
    
    staff_hours_fig.update_layout(
        title='Staff Hours by Month',
        xaxis_title='Month',
        yaxis_title='Hours',
        barmode='stack',
        height=400
    )
    
    staff_hours_json = json.dumps(staff_hours_fig, cls=PlotlyJSONEncoder)
    
    # Persona analysis radar chart
    persona_categories = ['Adherence', 'Engagement', 'Progress', 'Complexity', 'Satisfaction']
    persona_values = [random.randint(60, 95) for _ in persona_categories]
    
    persona_fig = go.Figure()
    
    persona_fig.add_trace(go.Scatterpolar(
        r=persona_values + [persona_values[0]],
        theta=persona_categories + [persona_categories[0]],
        fill='toself',
        name='Member Persona'
    ))
    
    persona_fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title='Member Persona Analysis',
        height=400
    )
    
    persona_json = json.dumps(persona_fig, cls=PlotlyJSONEncoder)
    dashboard = '''
       {% extends 'base.html' %}
{% block content %}
<div class="container-fluid">
    <div class="row mb-4">
        <div class="col-md-8">
            <h1>Get Better with Elyx Life!</h1>
            <h3>{{ profile.full_name if profile else session.username }}</h3>
        </div>
        <div class="col-md-4 text-end">
            <a href="{{ url_for('logout') }}" class="btn btn-outline-secondary">Logout</a>
        </div>
    </div>
    
    <div class="row mb-4">
        <div class="col-md-4">
            <div class="card h-100">
                <div class="card-header">
                    <h5>Your Profile</h5>
                </div>
                <div class="card-body">
                    {% if profile %}
                        <p><strong>Name : Rohan Patel</strong> </p>
                        <p><strong>DOB:</strong> {{ profile.dob }} (Age: {{ (2025 - datetime.strptime(profile.dob, '%Y-%m-%d').year) }})</p>
                        <p><strong>Gender:</strong> {{ profile.gender }}</p>
                        <p><strong>Location:</strong> {{ profile.location }}</p>
                        <p><strong>Occupation:</strong> {{ profile.occupation }}</p>
                        <p><strong>Chronic Condition:</strong> {{ profile.chronic_condition }}</p>
                        <hr>
                        <h6>Health Goals:</h6>
                        <ul>
                            {% for goal in profile.health_goals %}
                                <li>{{ goal }}</li>
                            {% endfor %}
                        </ul>
                    {% else %}
                        <div class="alert alert-warning">No profile information available.</div>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <div class="col-md-8">
            <div class="card h-100">
                <div class="card-header">
                    <h5>Recent Communications</h5>
                </div>
                <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                    {% if communications %}
                        {% for comm in communications %}
                            <div class="mb-3 p-2 {% if comm.sender == 'rohan' %}bg-light{% else %}bg-light-blue{% endif %}">
                                <div class="d-flex justify-content-between">
                                    <strong>{{ comm.sender }}</strong>
                                    <small class="text-muted">{{ comm.date }} ({{ comm.category }})</small>
                                </div>
                                <p class="mb-0">{{ comm.message }}</p>
                            </div>
                        {% endfor %}
                    {% else %}
                        <div class="alert alert-info">No communications found.</div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    
    <div class="row mb-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h5>Member Journey Timeline</h5>
                    <h5> 
                    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                    <h5> 
                </div>
                <div class="card-body">
                    <div id="timeline-chart" style="min-height: 300px;"></div>
                        {% if timeline_json %}
        <script>
            const timelineData = {{ timeline_json | safe }};
            Plotly.newPlot('timeline-chart', timelineData.data, timelineData.layout);
        </script>
        {% else %}
            <div class="alert alert-info">Timeline data not available</div>
        {% endif %}
        
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row mb-4">
        <div class="col-md-6">
            <div class="card h-100">
                <div class="card-header">
                    <h5>Persona Analysis</h5>
                </div>
                <div class="card-body">
                    <div id="persona-chart" style="min-height: 300px;">
                        {% if persona_json %}
    <script>
        const personaData = {{ persona_json | safe }};
        Plotly.newPlot("persona-chart", personaData.data, personaData.layout);
    </script>
    {% else %}
        <div class="alert alert-info">Persona analysis not available</div>
    {% endif %}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-6">
            <div class="card h-100">
                <div class="card-header">
                    <h5>Staff Activity Metrics</h5>
                </div>
                <div class="card-body">
                    <div id="staff-hours-chart" style="min-height: 300px;">
                        {% if staff_hours_json %}
<script>
    const staffHoursData = {{ staff_hours_json | safe }};
    Plotly.newPlot("staff-hours-chart", staffHoursData.data, staffHoursData.layout);
</script>
{% else %}
<div class="alert alert-info">Staff metrics not available</div>
{% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h5>Intervention Decision Explorer</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="list-group" style="max-height: 500px; overflow-y: auto;">
                                {% if interventions %}
                                    {% for intervention in interventions %}
                                        <a href="#" class="list-group-item list-group-item-action intervention-item" 
                                           data-id="{{ intervention.id }}"
                                           data-desc="{{ intervention.description }}"
                                           data-reason="{{ intervention.reason }}"
                                           data-outcome="{{ intervention.outcome }}"
                                           data-staff="{{ intervention.staff_member }}">
                                            {{ intervention.date }}: {{ intervention.type }} - {{ intervention.category }}
                                        </a>
                                    {% endfor %}
                                {% else %}
                                    <div class="alert alert-info"> no interventions </div>
                                {% endif %}
                            </div>
                        </div>
                        <div class="col-md-8">
                            <div id="intervention-detail" class="p-3 bg-light rounded" style="min-height: 200px;">
                                <h5>Select an intervention to view details</h5>
                                <p class="text-muted">Click on any intervention in the list to see the reasoning behind it and outcomes.</p>
                            </div>
                            <div class="mt-3">
                                <h5>Ask About This Decision</h5>
                                <div class="input-group mb-3">
                                    <input type="text" id="chat-question" class="form-control" placeholder="Ask why this decision was made...">
                                    <button class="btn btn-primary" id="ask-btn">Ask</button>
                                </div>
                                <div id="chat-response" class="p-3 bg-light rounded" style="min-height: 100px;">
                                    <p class="text-muted">Your answer will appear here.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // Initialize currentIntervention variable
    let currentIntervention = null;
    
    // Render Plotly charts if data exists
    document.addEventListener('DOMContentLoaded', function() {
        {% if timeline_json and timeline_json.data %}
            Plotly.newPlot('timeline-chart', {{ timeline_json | safe }}.data, {{ timeline_json | safe }}.layout);
        {% endif %}
        
        {% if staff_hours_json and staff_hours_json.data %}
            Plotly.newPlot('staff-hours-chart', {{ staff_hours_json | safe }}.data, {{ staff_hours_json | safe }}.layout);
        {% endif %}
        
        {% if persona_json and persona_json.data %}
            Plotly.newPlot('persona-chart', {{ persona_json | safe }}.data, {{ persona_json | safe }}.layout);
        {% endif %}
    });
    
    // Intervention detail viewer
    document.querySelectorAll('.intervention-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            const desc = this.getAttribute('data-desc');
            const reason = this.getAttribute('data-reason');
            const outcome = this.getAttribute('data-outcome');
            const staff = this.getAttribute('data-staff');
            
            document.getElementById('intervention-detail').innerHTML = `
                <h4>${desc}</h4>
                <p><strong>Staff Member:</strong> ${staff}</p>
                <div class="card mt-3">
                    <div class="card-header">
                        <h6>Reason for Decision</h6>
                    </div>
                    <div class="card-body">
                        <p>${reason}</p>
                    </div>
                </div>
                <div class="card mt-3">
                    <div class="card-header">
                        <h6>Outcome</h6>
                    </div>
                    <div class="card-body">
                        <p>${outcome || 'Outcome not yet recorded'}</p>
                    </div>
                </div>
            `;
            
            // Store current intervention for chat
            currentIntervention = {
                desc: desc,
                reason: reason,
                outcome: outcome,
                staff: staff
            };
        });
    });
    
    // Chat assistant functionality
    document.getElementById('ask-btn').addEventListener('click', function() {
        const question = document.getElementById('chat-question').value;
        if (!currentIntervention) {
            document.getElementById('chat-response').innerHTML = `
                <div class="alert alert-warning">Please select an intervention first.</div>
            `;
            return;
        }
        
        let response = `
            <strong>Intervention:</strong> ${currentIntervention.desc}<br>
            <strong>Staff Member:</strong> ${currentIntervention.staff}<br><br>
            <strong>Clinical Rationale:</strong> ${currentIntervention.reason}<br>
        `;
        
        if (currentIntervention.outcome && currentIntervention.outcome !== 'Outcome not yet recorded') {
            response += `<strong>Outcome Observed:</strong> ${currentIntervention.outcome}<br>`;
        }
        
        if (question.toLowerCase().includes('why')) {
            response += `<br><em>This decision was made because:</em> ${currentIntervention.reason}`;
        } else if (question.toLowerCase().includes('outcome') || question.toLowerCase().includes('result')) {
            response += `<br><em>The outcome was:</em> ${currentIntervention.outcome || 'not yet recorded'}`;
        } else if (question.toLowerCase().includes('who')) {
            response += `<br><em>This intervention was performed by:</em> ${currentIntervention.staff}`;
        } else {
            response += `<br><em>Based on your question:</em> The clinical team determined this was the appropriate intervention because ${currentIntervention.reason}`;
        }
        
        document.getElementById('chat-response').innerHTML = `
            <div class="alert alert-info">
                ${response}
            </div>
        `;
    });
</script>
{% endblock %}, profile=profile, communications=communications, interventions=interventions, 
       staff_metrics=staff_metrics, timeline_json=timeline_json, 
       staff_hours_json=staff_hours_json, persona_json=persona_json)
'''
    return render_template_string(
    dashboard,
    profile=profile,
    communications=communications,
    timeline_json = timeline_json,
    interventions=interventions,
    staff_metrics=staff_metrics,
    staff_hours_json=staff_hours_json,
    persona_json = persona_json
)
# Base template
base_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elyx Member Journey Visualization</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
    :root {
    --primary-color: #6f42c1;   /* Purple */
    --secondary-color: #f3e8ff; /* Light lavender */
    --hover-color: #e2d6f5;
    --text-color: #2d2d2d;
}
    body {
        padding-top: 20px;
        background-color: var(--secondary-color);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #333;
    }

    .bg-light-blue {
        background-color: #e7f5ff;
        border-left: 4px solid #0d6efd;
        border-radius: 8px;
        padding: 10px;
        transition: all 0.2s ease-in-out;
    }

    .bg-light-blue:hover {
        background-color: var(--secondary-color);
    border-left: 4px solid var(--primary-color);
        transform: translateX(4px);
    }

    .card {
        margin-bottom: 20px;
        border: none;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transition: transform 0.2s ease;
    }

    .card:hover {
        transform: translateY(-3px);
    }

    .card-header {
        background: linear-gradient(135deg, var(--primary-color), #512a9d);
        color: white;
        font-weight: 600;
        font-size: 1.1rem;
        padding: 12px 16px;
    }

    .card-body {
        padding: 16px;
        background-color: white;
    }

    .intervention-item {
        cursor: pointer;
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 8px;
        transition: background-color 0.2s ease;
    }

    .intervention-item:hover {
        background-color: #f1f3f5;
    }

    .alert-info {
        border-radius: 8px;
        background-color: #e9f5ff;
        color: #084298;
        padding: 12px;
        font-size: 0.95rem;
    }

    strong {
        color: var(--primary-color);
    }

    .text-muted {
        font-size: 0.85rem;
    }
</style>

</head>
<body>
    {% block content %}{% endblock %}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

app.jinja_loader = DictLoader({
    'base.html': base_template,
    'dashboard.html': dashboard
})

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=5001, debug=True)





