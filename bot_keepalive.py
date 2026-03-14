import time
from flask import Flask, request, session, redirect, render_template_string, jsonify
from threading import Thread
import os

app = Flask(__name__)
app.secret_key = os.urandom(24) # Secure session key

start_time = time.time()
bot_stats = {"messages_processed": 0, "compressions_done": 0}

# Global dummy settings for the web dashboard UI
web_settings = {
    "auto_research": True,
    "max_sarcasm": True,
    "nsfw_filter": True,
    "active_model": "llama-3.3-70b-versatile"
}

ADMIN_PASSWORD = "klein2026" # Change your web dashboard password here!

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Klein | Omni-Core Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --glass-bg: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
            --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            --accent: #00FFAA;
            --accent-glow: 0 0 15px rgba(0, 255, 170, 0.5);
            --text-main: #FFFFFF;
            --text-muted: #A0AEC0;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Poppins', sans-serif;
        }

        body {
            background: linear-gradient(135deg, #0f172a, #1e1b4b, #020617);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            overflow-x: hidden;
        }

        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* Glassmorphism Classes */
        .glass-panel {
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            box-shadow: var(--glass-shadow);
        }

        /* --- LOGIN SCREEN --- */
        #login-screen {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px;
            width: 90%;
            max-width: 400px;
            text-align: center;
            transition: opacity 0.5s ease;
        }

        .bot-avatar {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            border: 3px solid var(--accent);
            box-shadow: var(--accent-glow);
            margin-bottom: 20px;
            object-fit: cover;
        }

        h1 {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: 2px;
            margin-bottom: 5px;
        }

        .subtitle {
            color: var(--text-muted);
            font-size: 14px;
            margin-bottom: 30px;
        }

        input[type="password"] {
            width: 100%;
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border: 1px solid var(--glass-border);
            border-radius: 10px;
            color: white;
            font-size: 16px;
            outline: none;
            transition: all 0.3s ease;
            text-align: center;
            margin-bottom: 20px;
        }

        input[type="password"]:focus {
            border-color: var(--accent);
            box-shadow: var(--accent-glow);
        }

        button {
            width: 100%;
            padding: 15px;
            background: var(--accent);
            color: #000;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: var(--accent-glow);
        }

        /* --- DASHBOARD SCREEN --- */
        #dashboard-screen {
            display: none; /* Hidden until logged in */
            width: 95%;
            max-width: 1000px;
            padding: 30px;
            grid-template-columns: 250px 1fr;
            gap: 30px;
            opacity: 0;
            transition: opacity 0.5s ease;
        }

        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .sidebar-btn {
            background: transparent;
            color: var(--text-muted);
            text-align: left;
            padding: 15px 20px;
            border: 1px solid transparent;
        }

        .sidebar-btn.active, .sidebar-btn:hover {
            background: rgba(255,255,255,0.1);
            color: white;
            border-color: var(--glass-border);
        }

        .main-content {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }

        .stat-card {
            padding: 25px;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }

        .stat-val {
            font-size: 32px;
            font-weight: 800;
            color: var(--accent);
        }

        .stat-label {
            font-size: 14px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Settings Toggles */
        .setting-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid var(--glass-border);
        }

        .setting-info h3 { font-size: 18px; }
        .setting-info p { color: var(--text-muted); font-size: 13px; }

        /* Toggle Switch */
        .switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 28px;
        }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: rgba(0,0,0,0.5);
            transition: .4s;
            border-radius: 34px;
            border: 1px solid var(--glass-border);
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 20px;
            width: 20px;
            left: 4px;
            bottom: 3px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider { background-color: var(--accent); }
        input:checked + .slider:before { transform: translateX(20px); background-color: #000; }

        .footer {
            margin-top: 40px;
            text-align: center;
            font-size: 14px;
            color: var(--text-muted);
            letter-spacing: 1px;
        }
        .footer span { color: var(--accent); font-weight: 600; }

        @media (max-width: 768px) {
            #dashboard-screen { grid-template-columns: 1fr; }
            .sidebar { flex-direction: row; overflow-x: auto; }
            .sidebar-btn { text-align: center; flex: 1; }
        }
    </style>
</head>
<body>

    <!-- LOGIN SCREEN -->
    <div id="login-screen" class="glass-panel" {% if logged_in %}style="display:none;"{% endif %}>
        <!-- You can replace this URL with your bot's actual Discord avatar URL -->
        <img src="https://i.imgur.com/8Qz9f4u.png" alt="Klein Core" class="bot-avatar">
        <h1>KLEIN CORE</h1>
        <p class="subtitle">Secure Administrator Access</p>
        
        <form action="/login" method="POST" style="width: 100%;">
            <input type="password" name="password" placeholder="Enter Access Key" required>
            <button type="submit">INITIALIZE LOGIN</button>
        </form>
        {% if error %}<p style="color: #ff4444; margin-top: 15px; font-size: 14px;">{{ error }}</p>{% endif %}
    </div>

    <!-- DASHBOARD SCREEN -->
    <div id="dashboard-screen" class="glass-panel" {% if logged_in %}style="display:grid; opacity:1;"{% endif %}>
        
        <!-- Sidebar -->
        <div class="sidebar">
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="https://i.imgur.com/8Qz9f4u.png" style="width: 60px; height: 60px; border-radius: 50%; border: 2px solid var(--accent);">
                <h3 style="margin-top: 10px;">Klein Web</h3>
            </div>
            <button class="sidebar-btn active glass-panel">📊 Overview</button>
            <button class="sidebar-btn glass-panel" onclick="alert('Module locked in V1. Database connection required.')">⚙️ Global Config</button>
            <button class="sidebar-btn glass-panel" onclick="alert('Terminal access requires SSH protocol.')">💻 Web Terminal</button>
            <form action="/logout" method="POST" style="margin-top: auto;">
                <button type="submit" class="sidebar-btn glass-panel" style="width: 100%; color: #ff4444;">🚪 Logout</button>
            </form>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <h2 style="font-weight: 600; font-size: 24px;">System Overview</h2>
            
            <div class="stats-grid">
                <div class="stat-card glass-panel">
                    <div class="stat-val">{{ uptime }}h</div>
                    <div class="stat-label">Core Uptime</div>
                </div>
                <div class="stat-card glass-panel">
                    <div class="stat-val">{{ messages }}</div>
                    <div class="stat-label">Queries Processed</div>
                </div>
                <div class="stat-card glass-panel">
                    <div class="stat-val">{{ compressions }}</div>
                    <div class="stat-label">Memory Wipes</div>
                </div>
            </div>

            <div class="glass-panel" style="margin-top: 20px; padding: 10px;">
                <div class="setting-row">
                    <div class="setting-info">
                        <h3>Deep Web Research</h3>
                        <p>Allow Klein to automatically scrape DuckDuckGo for live facts.</p>
                    </div>
                    <label class="switch">
                        <input type="checkbox" checked>
                        <span class="slider"></span>
                    </label>
                </div>
                
                <div class="setting-row">
                    <div class="setting-info">
                        <h3>Max Sarcasm Protocol</h3>
                        <p>Forces the AI into the dry, unbothered 2026 human persona.</p>
                    </div>
                    <label class="switch">
                        <input type="checkbox" checked>
                        <span class="slider"></span>
                    </label>
                </div>

                <div class="setting-row" style="border-bottom: none;">
                    <div class="setting-info">
                        <h3>Active Engine</h3>
                        <p>Current brain powering the Omni-Core.</p>
                    </div>
                    <div style="color: var(--accent); font-weight: 600; background: rgba(0,0,0,0.3); padding: 8px 15px; border-radius: 8px;">
                        LLaMA 3.3 70B
                    </div>
                </div>
            </div>
        </div>

    </div>

    <div class="footer">
        Built by <span>Yathin</span> & <span>Google</span> 🚀
    </div>

</body>
</html>
"""

@app.route('/')
def home():
    uptime = round((time.time() - start_time) / 3600, 2)
    logged_in = session.get('logged_in', False)
    error = session.pop('error', None)
    
    return render_template_string(
        HTML_TEMPLATE,
        logged_in=logged_in,
        error=error,
        uptime=uptime,
        messages=bot_stats['messages_processed'],
        compressions=bot_stats['compressions_done']
    )

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        session['logged_in'] = True
    else:
        session['error'] = "ACCESS DENIED: Invalid Key."
    return redirect('/')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return redirect('/')

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()