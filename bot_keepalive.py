import time
import os
import json
import sqlite3
from flask import Flask, request, session, redirect, render_template_string, jsonify
from threading import Thread

app = Flask(__name__)
app.secret_key = os.urandom(24)

start_time = time.time()
bot_stats = {"messages_processed": 0, "compressions_done": 0, "api_calls": 0}

# Global UI & Bot Configuration
ui_config = {
    "avatar_url": "https://i.imgur.com/8Qz9f4u.png",
    "bg_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop", 
    "bot_status": "Bypassing Mainframes...",
}

ADMIN_PASSWORD = "klein2026"
DEV_PASSWORD = "mr_yaen"

# Helper to read DB without locking it
def get_db_stats():
    try:
        conn = sqlite3.connect("klein_database.db", timeout=1)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM chat_memory")
        mem_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM active_channels")
        chan_count = c.fetchone()[0]
        conn.close()
        return mem_count, chan_count
    except:
        return 0, 0

# ==========================================
# 🌐 THE FRONTEND (SPA, Chart.js, AJAX)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Klein Omni-Core | Master Control</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Fira+Code:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root { --primary: #00f0ff; --primary-dark: #0088ff; --glass-bg: rgba(10, 25, 50, 0.6); --glass-border: rgba(0, 240, 255, 0.2); --text-main: #ffffff; --text-muted: #8ab4f8; --danger: #ff3366; --success: #00ffaa; --warn: #ffaa00; }
        [data-theme="light"] { --primary: #0055ff; --primary-dark: #0033cc; --glass-bg: rgba(255, 255, 255, 0.8); --glass-border: rgba(0, 85, 255, 0.3); --text-main: #111827; --text-muted: #4b5563; }
        
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; transition: background-color 0.3s, color 0.3s; }
        body { background-image: url('{{ bg_url }}'); background-size: cover; background-position: center; background-attachment: fixed; color: var(--text-main); height: 100vh; display: flex; align-items: center; justify-content: center; overflow: hidden; }
        .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(5, 11, 20, 0.6); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); z-index: -1; }
        .glass { background: var(--glass-bg); backdrop-filter: blur(25px); border: 1px solid var(--glass-border); border-radius: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }
        
        /* LOGIN */
        #login-container { width: 100%; max-width: 400px; padding: 40px; text-align: center; z-index: 10; }
        .avatar { width: 110px; height: 110px; border-radius: 50%; border: 3px solid var(--primary); margin-bottom: 20px; box-shadow: 0 0 20px var(--primary-dark); }
        .input-group { position: relative; margin-bottom: 20px; }
        .input-group i { position: absolute; left: 15px; top: 50%; transform: translateY(-50%); color: var(--primary); }
        input { width: 100%; padding: 15px 15px 15px 45px; background: rgba(0,0,0,0.3); border: 1px solid var(--glass-border); border-radius: 12px; color: var(--text-main); font-size: 16px; outline: none; }
        input:focus { border-color: var(--primary); box-shadow: 0 0 10px rgba(0,240,255,0.3); }
        .btn { width: 100%; padding: 15px; background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: #fff; border: none; border-radius: 12px; font-size: 16px; font-weight: 700; cursor: pointer; text-transform: uppercase; box-shadow: 0 5px 15px rgba(0,240,255,0.4); }
        .btn:hover { transform: translateY(-2px); }

        /* DASHBOARD */
        #dashboard-container { width: 98%; max-width: 1400px; height: 95vh; display: grid; grid-template-columns: 280px 1fr; gap: 20px; padding: 20px; z-index: 10; }
        
        /* SIDEBAR */
        .sidebar { padding: 30px 20px; display: flex; flex-direction: column; gap: 10px; overflow-y: auto; }
        .nav-header { text-align: center; margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid var(--glass-border); }
        .nav-header img { width: 70px; height: 70px; border-radius: 50%; border: 2px solid var(--primary); }
        .nav-btn { background: transparent; color: var(--text-muted); border: none; padding: 15px; border-radius: 12px; text-align: left; font-size: 16px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 15px; }
        .nav-btn:hover, .nav-btn.active { background: var(--glass-border); color: var(--text-main); border-left: 4px solid var(--primary); }
        
        /* CONTENT */
        .content-area { padding: 30px; overflow-y: auto; position: relative; }
        .content-area::-webkit-scrollbar { width: 6px; }
        .content-area::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }
        
        .tab { display: none; animation: slideIn 0.4s ease; }
        .tab.active { display: block; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .header-bar h2 { font-size: 28px; font-weight: 800; }
        .controls { display: flex; gap: 15px; }
        .icon-btn { background: var(--glass-border); border: none; color: var(--text-main); width: 45px; height: 45px; border-radius: 12px; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; transition: 0.3s; }
        .icon-btn:hover { background: var(--primary); box-shadow: 0 0 15px var(--primary); }

        /* WIDGETS */
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 25px; }
        .widget { padding: 25px; border-radius: 16px; border-top: 3px solid var(--primary); position: relative; overflow: hidden; }
        .widget-val { font-size: 38px; font-weight: 900; margin-bottom: 5px; font-family: 'Fira Code', monospace; }
        .widget-label { font-size: 13px; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 1px; }
        .widget-icon { position: absolute; right: 20px; top: 25px; font-size: 40px; opacity: 0.1; color: var(--primary); }

        /* CHART */
        .chart-container { width: 100%; height: 300px; padding: 20px; border-radius: 16px; margin-bottom: 25px; }

        /* TERMINAL */
        .terminal { background: rgba(0,0,0,0.8); border-radius: 12px; padding: 20px; height: 350px; overflow-y: auto; font-family: 'Fira Code', monospace; font-size: 14px; border: 1px solid var(--glass-border); }
        .t-line { margin-bottom: 8px; color: #a0aec0; }
        .t-prefix { color: #3b82f6; font-weight: bold; }
        .t-success { color: var(--success); }
        .t-warn { color: var(--warn); }
        .t-danger { color: var(--danger); }

        /* TOAST */
        #toast { position: fixed; bottom: 30px; right: 30px; background: var(--glass-bg); backdrop-filter: blur(10px); border-left: 4px solid var(--primary); padding: 15px 25px; border-radius: 8px; color: white; transform: translateX(150%); transition: 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55); z-index: 100; box-shadow: 0 10px 30px rgba(0,0,0,0.5); font-weight: 600; }
        #toast.show { transform: translateX(0); }

        /* SETTINGS ROWS */
        .setting-row { display: flex; justify-content: space-between; align-items: center; padding: 20px; background: rgba(0,0,0,0.2); border-radius: 12px; margin-bottom: 15px; border: 1px solid transparent; }
        .setting-row:hover { border-color: var(--glass-border); }

        @media (max-width: 900px) {
            #dashboard-container { grid-template-columns: 1fr; height: auto; display: flex; flex-direction: column; overflow-y: auto; }
            .sidebar { flex-direction: row; flex-wrap: wrap; justify-content: center; padding: 15px; border-radius: 16px; }
            .nav-header { display: none; }
            .nav-btn { flex: 1; min-width: 100px; flex-direction: column; font-size: 12px; padding: 10px; gap: 5px; text-align: center; justify-content: center; }
        }
    </style>
</head>
<body>
    <div class="overlay"></div>

    <!-- LOGIN -->
    {% if not logged_in %}
    <div id="login-container" class="glass">
        <img src="{{ avatar_url }}" class="avatar">
        <h1>OMNI-CORE</h1><p class="subtitle">Enter master credentials to establish uplink.</p>
        <form action="/login" method="POST">
            <div class="input-group"><i class="fa-solid fa-fingerprint"></i><input type="password" name="password" placeholder="Access Key" required></div>
            <button type="submit" class="btn">Authenticate</button>
        </form>
        {% if error %}<p style="color: var(--danger); margin-top: 20px; font-weight: 600;">{{ error }}</p>{% endif %}
    </div>
    {% endif %}

    <!-- DASHBOARD -->
    {% if logged_in %}
    <div id="dashboard-container">
        <!-- SIDEBAR -->
        <div class="sidebar glass">
            <div class="nav-header">
                <img src="{{ avatar_url }}">
                <h3 style="margin-top: 10px;">{{ 'Dev Protocol' if role == 'dev' else 'Admin Access' }}</h3>
                <span style="color: var(--success); font-size: 12px; font-weight: 800;">● LIVE</span>
            </div>
            <button class="nav-btn active" onclick="switchTab('overview')"><i class="fa-solid fa-chart-line"></i> Analytics</button>
            <button class="nav-btn" onclick="switchTab('database')"><i class="fa-solid fa-database"></i> Database</button>
            <button class="nav-btn" onclick="switchTab('terminal')"><i class="fa-solid fa-terminal"></i> Terminal</button>
            {% if role == 'dev' %}
            <button class="nav-btn" style="color: var(--warn);" onclick="switchTab('devpanel')"><i class="fa-solid fa-code"></i> Dev Console</button>
            {% endif %}
            <form action="/logout" method="POST" style="margin-top: auto;">
                <button type="submit" class="nav-btn" style="width: 100%; color: var(--danger); justify-content: center;"><i class="fa-solid fa-power-off"></i> Disconnect</button>
            </form>
        </div>

        <!-- MAIN CONTENT -->
        <div class="content-area glass">
            
            <div class="header-bar">
                <h2 id="page-title">Network Analytics</h2>
                <div class="controls">
                    <button class="icon-btn" onclick="fetchData()"><i class="fa-solid fa-rotate-right"></i></button>
                    <button class="icon-btn" onclick="toggleTheme()"><i class="fa-solid fa-moon" id="theme-icon"></i></button>
                </div>
            </div>

            <!-- OVERVIEW TAB -->
            <div id="overview" class="tab active">
                <div class="grid-3">
                    <div class="widget glass">
                        <i class="fa-solid fa-stopwatch widget-icon"></i>
                        <div class="widget-val" id="val-uptime">--</div>
                        <div class="widget-label">System Uptime</div>
                    </div>
                    <div class="widget glass">
                        <i class="fa-solid fa-microchip widget-icon"></i>
                        <div class="widget-val" id="val-msgs">--</div>
                        <div class="widget-label">Queries Processed</div>
                    </div>
                    <div class="widget glass" style="border-top-color: var(--warn);">
                        <i class="fa-solid fa-server widget-icon"></i>
                        <div class="widget-val" id="val-apis">--</div>
                        <div class="widget-label">API Calls Made</div>
                    </div>
                </div>

                <div class="chart-container glass">
                    <canvas id="trafficChart"></canvas>
                </div>
            </div>

            <!-- DATABASE TAB -->
            <div id="database" class="tab">
                <div class="grid-3">
                    <div class="widget glass" style="border-top-color: #a855f7;">
                        <i class="fa-solid fa-memory widget-icon"></i>
                        <div class="widget-val" id="val-mem">--</div>
                        <div class="widget-label">Active Memory Rows</div>
                    </div>
                    <div class="widget glass" style="border-top-color: #3b82f6;">
                        <i class="fa-solid fa-hashtag widget-icon"></i>
                        <div class="widget-val" id="val-chan">--</div>
                        <div class="widget-label">Auto-Chat Channels</div>
                    </div>
                </div>
                
                <div class="glass" style="padding: 30px; border-radius: 16px;">
                    <h3 style="margin-bottom: 15px; color: var(--danger);"><i class="fa-solid fa-triangle-exclamation"></i> Danger Zone</h3>
                    <p style="color: var(--text-muted); margin-bottom: 20px;">Manual database intervention. These actions cannot be undone.</p>
                    <button class="btn" style="background: var(--danger); width: auto; padding: 12px 25px;" onclick="apiAction('wipe_mem')">Wipe Chat Memory</button>
                    <button class="btn" style="background: transparent; border: 1px solid var(--danger); color: var(--danger); width: auto; padding: 12px 25px; margin-left: 10px;" onclick="apiAction('wipe_chan')">Clear Auto-Channels</button>
                </div>
            </div>

            <!-- TERMINAL TAB -->
            <div id="terminal" class="tab">
                <div class="terminal" id="term-box">
                    <div class="t-line"><span class="t-prefix">root@omni:~#</span> Connection established. Listening on port 8080.</div>
                </div>
            </div>

            <!-- DEV PANEL TAB -->
            {% if role == 'dev' %}
            <div id="devpanel" class="tab">
                <div class="glass" style="padding: 30px; border-radius: 16px; margin-bottom: 20px; border: 1px solid var(--warn);">
                    <h3 style="margin-bottom: 20px; color: var(--warn);"><i class="fa-solid fa-paint-roller"></i> Global UI Overrides</h3>
                    <form action="/update_dev" method="POST">
                        <div class="input-group">
                            <i class="fa-solid fa-image"></i>
                            <input type="text" name="avatar_url" value="{{ avatar_url }}" placeholder="Avatar Link">
                        </div>
                        <div class="input-group">
                            <i class="fa-solid fa-desktop"></i>
                            <input type="text" name="bg_url" value="{{ bg_url }}" placeholder="Background Link">
                        </div>
                        <div class="input-group">
                            <i class="fa-solid fa-gamepad"></i>
                            <input type="text" name="bot_status" value="{{ bot_status }}" placeholder="Bot 'Playing' Status">
                        </div>
                        <button type="submit" class="btn" style="background: linear-gradient(135deg, #ffaa00, #ff6600);">Deploy Configuration</button>
                    </form>
                </div>
            </div>
            {% endif %}

        </div>
    </div>
    
    <!-- TOAST ALERT -->
    <div id="toast">Notification</div>

    <script>
        // --- 1. UI LOGIC ---
        function switchTab(tabId) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
            
            const titles = { 'overview': 'Network Analytics', 'database': 'Database Core', 'terminal': 'Live Logs', 'devpanel': 'Developer Console' };
            document.getElementById('page-title').innerText = titles[tabId];
        }

        function toggleTheme() {
            const html = document.documentElement;
            const icon = document.getElementById('theme-icon');
            if (html.getAttribute('data-theme') === 'dark') {
                html.setAttribute('data-theme', 'light');
                icon.className = 'fa-solid fa-sun';
            } else {
                html.setAttribute('data-theme', 'dark');
                icon.className = 'fa-solid fa-moon';
            }
        }

        function showToast(msg, isError=false) {
            const toast = document.getElementById('toast');
            toast.innerText = msg;
            toast.style.borderLeftColor = isError ? 'var(--danger)' : 'var(--primary)';
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
            logTerminal(msg, isError ? 't-danger' : 't-success');
        }

        // --- 2. TERMINAL LOGIC ---
        const termBox = document.getElementById('term-box');
        function logTerminal(msg, colorClass='t-line') {
            if(!termBox) return;
            const time = new Date().toLocaleTimeString();
            termBox.innerHTML += `<div class="${colorClass}"><span class="t-prefix">[${time}] sys@omni:~$</span> ${msg}</div>`;
            termBox.scrollTop = termBox.scrollHeight;
        }

        // --- 3. CHART.JS LOGIC ---
        let chart;
        const ctx = document.getElementById('trafficChart');
        if(ctx) {
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['10s', '8s', '6s', '4s', '2s', 'Now'],
                    datasets: [{
                        label: 'API Requests / Sec',
                        data: [0, 0, 0, 0, 0, 0],
                        borderColor: '#00f0ff',
                        backgroundColor: 'rgba(0, 240, 255, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } },
                    plugins: { legend: { labels: { color: '#8ab4f8' } } }
                }
            });
        }

        // --- 4. AJAX DATA FETCHING (No Reloads!) ---
        async function fetchData() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                
                // Update Widgets
                document.getElementById('val-uptime').innerText = data.uptime + 'h';
                document.getElementById('val-msgs').innerText = data.msgs;
                document.getElementById('val-apis').innerText = data.apis;
                document.getElementById('val-mem').innerText = data.db_mem;
                document.getElementById('val-chan').innerText = data.db_chan;

                // Update Chart (Simulating active load based on total msgs changing)
                if(chart) {
                    const newLoad = Math.floor(Math.random() * 5); // Simulated spike
                    chart.data.datasets[0].data.shift();
                    chart.data.datasets[0].data.push(newLoad);
                    chart.update();
                }
            } catch (e) { console.error("API Fetch Error"); }
        }

        // --- 5. ACTION EXECUTOR ---
        async function apiAction(action) {
            if(!confirm("Are you sure? This directly alters the database.")) return;
            try {
                const res = await fetch(`/api/action?type=${action}`);
                const data = await res.json();
                showToast(data.message, data.status !== 'success');
                fetchData(); // Refresh stats immediately
            } catch(e) { showToast("Action failed to execute.", true); }
        }

        // Auto-refresh data every 3 seconds
        if(document.getElementById('val-uptime')) {
            fetchData();
            setInterval(fetchData, 3000);
            
            // Random terminal noise
            setInterval(() => {
                if(Math.random() > 0.7) logTerminal("Heartbeat ping: 24ms", "t-line");
            }, 5000);
        }
    </script>
    {% endif %}
</body>
</html>
"""

# ==========================================
# ⚙️ FLASK ROUTES & API
# ==========================================
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, 
        logged_in=session.get('logged_in', False), 
        role=session.get('role', 'admin'), 
        error=session.pop('error', None), 
        avatar_url=ui_config['avatar_url'], 
        bg_url=ui_config['bg_url'],
        bot_status=ui_config['bot_status']
    )

@app.route('/login', methods=['POST'])
def login():
    pw = request.form.get('password', '').strip() 
    if pw == ADMIN_PASSWORD: 
        session['logged_in'], session['role'] = True, 'admin'
    elif pw == DEV_PASSWORD: 
        session['logged_in'], session['role'] = True, 'dev'
    else: 
        session['error'] = "ACCESS DENIED: Invalid Security Key."
    return redirect('/')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')

@app.route('/update_dev', methods=['POST'])
def update_dev():
    if session.get('role') == 'dev':
        ui_config['avatar_url'] = request.form.get('avatar_url', ui_config['avatar_url']).strip()
        ui_config['bg_url'] = request.form.get('bg_url', ui_config['bg_url']).strip()
        ui_config['bot_status'] = request.form.get('bot_status', ui_config['bot_status']).strip()
    return redirect('/')

# --- AJAX API ENDPOINTS ---
@app.route('/api/stats')
def api_stats():
    if not session.get('logged_in'): return jsonify({"error": "unauthorized"}), 401
    
    mem_c, chan_c = get_db_stats()
    return jsonify({
        "uptime": round((time.time() - start_time) / 3600, 2),
        "msgs": bot_stats['messages_processed'],
        "apis": bot_stats['api_calls'],
        "db_mem": mem_c,
        "db_chan": chan_c
    })

@app.route('/api/action')
def api_action():
    if session.get('role') != 'dev' and session.get('role') != 'admin': 
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    action_type = request.args.get('type')
    try:
        conn = sqlite3.connect("klein_database.db")
        c = conn.cursor()
        
        if action_type == 'wipe_mem':
            c.execute("DELETE FROM chat_memory")
            msg = "Chat memory successfully purged."
        elif action_type == 'wipe_chan':
            c.execute("DELETE FROM active_channels")
            msg = "Auto-channels cleared."
        else:
            conn.close()
            return jsonify({"status": "error", "message": "Unknown action"}), 400
            
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": msg})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()