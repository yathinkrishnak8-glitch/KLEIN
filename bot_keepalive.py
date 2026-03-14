import time
from flask import Flask, request, session, redirect, render_template_string
from threading import Thread
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

start_time = time.time()
bot_stats = {"messages_processed": 0, "compressions_done": 0}

ui_config = {
    "avatar_url": "https://i.imgur.com/8Qz9f4u.png",
    "bg_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop", 
    "deep_search": True,
    "max_sarcasm": True,
}

ADMIN_PASSWORD = "klein2026"
DEV_PASSWORD = "mr_yaen"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Klein Omni-Core | Liquid Interface</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --primary: #00f0ff; --primary-dark: #0088ff; --glass-bg: rgba(10, 25, 50, 0.4); --glass-border: rgba(0, 240, 255, 0.2); --glass-highlight: rgba(255, 255, 255, 0.05); --shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5); --text-main: #ffffff; --text-muted: #8ab4f8; --danger: #ff3366; --success: #00ffaa; }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }
        body { background-color: #050b14; background-image: url('{{ bg_url }}'); background-size: cover; background-position: center; background-attachment: fixed; color: var(--text-main); min-height: 100vh; display: flex; align-items: center; justify-content: center; backdrop-filter: brightness(0.4) blur(5px); -webkit-backdrop-filter: brightness(0.4) blur(5px); }
        .glass { background: var(--glass-bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid var(--glass-border); border-top: 1px solid rgba(255,255,255,0.2); border-left: 1px solid rgba(255,255,255,0.1); border-radius: 24px; box-shadow: var(--shadow); }
        #login-container { width: 100%; max-width: 450px; padding: 50px 40px; text-align: center; }
        .avatar-container { position: relative; width: 130px; height: 130px; margin: 0 auto 25px auto; }
        .bot-avatar { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; border: 3px solid var(--primary); box-shadow: 0 0 25px rgba(0, 240, 255, 0.5); position: relative; z-index: 2; }
        .avatar-ring { position: absolute; top: -10px; left: -10px; right: -10px; bottom: -10px; border-radius: 50%; border: 2px dashed var(--primary-dark); animation: spin 10s linear infinite; z-index: 1; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        h1 { font-size: 36px; font-weight: 900; letter-spacing: 2px; text-shadow: 0 0 10px rgba(0,240,255,0.5); margin-bottom: 5px; }
        .subtitle { color: var(--text-muted); font-size: 15px; font-weight: 300; margin-bottom: 40px; letter-spacing: 1px; }
        .input-group { position: relative; margin-bottom: 25px; }
        .input-group i { position: absolute; left: 20px; top: 50%; transform: translateY(-50%); color: var(--primary); font-size: 18px; }
        input[type="password"], input[type="text"] { width: 100%; padding: 18px 20px 18px 50px; background: rgba(0, 0, 0, 0.4); border: 1px solid var(--glass-border); border-radius: 15px; color: white; font-size: 16px; outline: none; transition: 0.3s; }
        input:focus { border-color: var(--primary); box-shadow: 0 0 15px rgba(0,240,255,0.3); background: rgba(0,0,0,0.6); }
        .btn { width: 100%; padding: 18px; background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: #000; border: none; border-radius: 15px; font-size: 18px; font-weight: 700; cursor: pointer; transition: 0.3s; text-transform: uppercase; letter-spacing: 1.5px; box-shadow: 0 5px 20px rgba(0, 240, 255, 0.4); }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0, 240, 255, 0.6); }
        #dashboard-container { width: 95%; max-width: 1400px; height: 90vh; display: grid; grid-template-columns: 280px 1fr; gap: 25px; opacity: 0; display: none; animation: fadeIn 0.8s forwards; }
        @keyframes fadeIn { to { opacity: 1; } }
        .sidebar { display: flex; flex-direction: column; padding: 30px 20px; gap: 15px; }
        .nav-header { text-align: center; margin-bottom: 30px; border-bottom: 1px solid var(--glass-border); padding-bottom: 20px; }
        .nav-header img { width: 70px; height: 70px; border-radius: 50%; border: 2px solid var(--primary); margin-bottom: 10px; }
        .nav-btn { background: transparent; color: var(--text-muted); border: none; padding: 15px 20px; border-radius: 12px; text-align: left; font-size: 16px; font-weight: 500; cursor: pointer; transition: 0.3s; display: flex; align-items: center; gap: 15px; }
        .nav-btn:hover { background: var(--glass-highlight); color: white; transform: translateX(5px); }
        .nav-btn.active { background: linear-gradient(90deg, rgba(0,240,255,0.1), transparent); border-left: 4px solid var(--primary); color: var(--primary); }
        .role-badge { margin-top: auto; padding: 15px; background: rgba(0,0,0,0.4); border-radius: 12px; text-align: center; font-size: 14px; border: 1px solid var(--glass-border); }
        .role-badge span { color: var(--primary); font-weight: 700; text-transform: uppercase; }
        .content-area { padding: 30px; overflow-y: auto; display: flex; flex-direction: column; gap: 30px; }
        .tab-section { display: none; animation: slideUp 0.5s ease; }
        .tab-section.active { display: block; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        h2.section-title { font-size: 28px; font-weight: 700; margin-bottom: 20px; display: flex; align-items: center; gap: 15px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .stat-card { padding: 25px; border-radius: 20px; position: relative; overflow: hidden; }
        .stat-card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: linear-gradient(90deg, var(--primary), transparent); }
        .stat-val { font-size: 42px; font-weight: 900; color: white; margin-bottom: 5px; display: flex; align-items: center; gap: 10px; }
        .stat-label { font-size: 14px; color: var(--text-muted); font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }
        .setting-row { display: flex; justify-content: space-between; align-items: center; padding: 25px; background: rgba(0,0,0,0.2); border-radius: 16px; margin-bottom: 15px; border: 1px solid transparent; transition: 0.3s; }
        .setting-row:hover { border-color: var(--glass-border); background: rgba(0,0,0,0.4); }
        .setting-info h3 { font-size: 18px; margin-bottom: 5px; color: white; }
        .setting-info p { font-size: 14px; color: var(--text-muted); }
        .toggle { position: relative; width: 60px; height: 32px; appearance: none; background: rgba(255,255,255,0.1); border-radius: 32px; outline: none; cursor: pointer; transition: 0.4s; box-shadow: inset 0 0 5px rgba(0,0,0,0.5); }
        .toggle::after { content: ''; position: absolute; top: 3px; left: 3px; width: 26px; height: 26px; border-radius: 50%; background: #fff; transition: 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55); box-shadow: 0 2px 5px rgba(0,0,0,0.3); }
        .toggle:checked { background: var(--primary); box-shadow: 0 0 15px rgba(0,240,255,0.4); }
        .toggle:checked::after { transform: translateX(28px); }
        .metric-group { margin-bottom: 20px; }
        .metric-header { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; font-weight: 600; }
        .progress-bar { width: 100%; height: 10px; background: rgba(255,255,255,0.1); border-radius: 5px; overflow: hidden; }
        .progress-fill { height: 100%; background: var(--primary); border-radius: 5px; box-shadow: 0 0 10px var(--primary); transition: width 1s ease; }
        .dev-form label { display: block; margin-bottom: 8px; font-weight: 500; color: var(--text-muted); }
        .dev-form button { margin-top: 15px; width: auto; padding: 12px 30px; }
        .footer-tag { text-align: center; margin-top: 40px; font-size: 13px; color: rgba(255,255,255,0.4); letter-spacing: 2px; }
        .footer-tag span { color: var(--primary); font-weight: 700; }
        @media (max-width: 900px) {
            #dashboard-container { grid-template-columns: 1fr; height: auto; display: block; }
            .sidebar { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; padding: 20px; margin-bottom: 20px; }
            .nav-header, .role-badge, .sidebar form { display: none; }
            .nav-btn { text-align: center; justify-content: center; padding: 15px 10px; flex-direction: column; gap: 5px; font-size: 12px; }
            .stat-val { font-size: 32px; }
        }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div id="login-container" class="glass">
        <div class="avatar-container"><div class="avatar-ring"></div><img src="{{ avatar_url }}" class="bot-avatar"></div>
        <h1>KLEIN CORE</h1><p class="subtitle">Enter access credentials to sync.</p>
        <form action="/login" method="POST">
            <div class="input-group"><i class="fa-solid fa-lock"></i><input type="password" name="password" placeholder="System Key / Dev Key" required></div>
            <button type="submit" class="btn">Initialize Link</button>
        </form>
        {% if error %}<p style="color: var(--danger); margin-top: 20px; font-weight: 600; font-size: 14px;">{{ error }}</p>{% endif %}
    </div>
    {% endif %}

    {% if logged_in %}
    <div id="dashboard-container" style="display: grid;">
        <div class="sidebar glass">
            <div class="nav-header"><img src="{{ avatar_url }}"><h3>Omni-Core Node</h3><p style="font-size: 12px; color: var(--success);">🟢 Connection Stable</p></div>
            <button class="nav-btn active" onclick="switchTab('overview')"><i class="fa-solid fa-chart-line"></i> Overview</button>
            <button class="nav-btn" onclick="switchTab('settings')"><i class="fa-solid fa-sliders"></i> Engine Config</button>
            {% if role == 'dev' %}<button class="nav-btn" style="color: #ffaa00;" onclick="switchTab('developer')"><i class="fa-solid fa-code"></i> Dev Tools</button>{% endif %}
            <div class="role-badge">Access Level: <span>{{ 'Developer' if role == 'dev' else 'Administrator' }}</span></div>
            <form action="/logout" method="POST" style="margin-top: 15px;"><button type="submit" class="nav-btn" style="width: 100%; justify-content: center; color: var(--danger);"><i class="fa-solid fa-power-off"></i> Disconnect</button></form>
        </div>

        <div class="content-area glass">
            <div id="overview" class="tab-section active">
                <h2 class="section-title"><i class="fa-solid fa-satellite-dish"></i> Live Telemetry</h2>
                <div class="stats-grid">
                    <div class="stat-card glass"><div class="stat-val"><i class="fa-solid fa-clock" style="font-size: 24px; opacity: 0.5;"></i> {{ uptime }}h</div><div class="stat-label">System Uptime</div></div>
                    <div class="stat-card glass"><div class="stat-val"><i class="fa-solid fa-microchip" style="font-size: 24px; opacity: 0.5;"></i> {{ messages }}</div><div class="stat-label">Total Queries</div></div>
                    <div class="stat-card glass"><div class="stat-val"><i class="fa-solid fa-database" style="font-size: 24px; opacity: 0.5;"></i> {{ compressions }}</div><div class="stat-label">Memory Compressions</div></div>
                </div>
                <h2 class="section-title" style="margin-top: 40px;"><i class="fa-solid fa-server"></i> Hardware Simulation</h2>
                <div class="glass" style="padding: 30px; border-radius: 20px;">
                    <div class="metric-group"><div class="metric-header"><span>CPU Load (Groq LPU)</span> <span id="cpu-val">42%</span></div><div class="progress-bar"><div class="progress-fill" id="cpu-bar" style="width: 42%;"></div></div></div>
                    <div class="metric-group"><div class="metric-header"><span>Memory Allocation</span> <span id="ram-val">1.2 GB / 8.0 GB</span></div><div class="progress-bar"><div class="progress-fill" id="ram-bar" style="width: 15%; background: #a855f7;"></div></div></div>
                </div>
            </div>

            <div id="settings" class="tab-section">
                <h2 class="section-title"><i class="fa-solid fa-layer-group"></i> Logic Toggles</h2>
                <div class="setting-row"><div class="setting-info"><h3>Deep Web Scraping</h3><p>Allows DuckDuckGo integration for real-time facts.</p></div><input type="checkbox" class="toggle" checked></div>
                <div class="setting-row"><div class="setting-info"><h3>Dry Sarcasm Engine</h3><p>Enforces the 2026 unbothered human persona.</p></div><input type="checkbox" class="toggle" checked></div>
            </div>

            {% if role == 'dev' %}
            <div id="developer" class="tab-section">
                <h2 class="section-title" style="color: #ffaa00;"><i class="fa-solid fa-code"></i> Developer Override</h2>
                <div class="glass" style="padding: 30px; border-radius: 20px; border-color: rgba(255, 170, 0, 0.3);">
                    <form action="/update_dev" method="POST" class="dev-form">
                        <div class="input-group"><label>Bot Avatar Image URL</label><i class="fa-solid fa-image"></i><input type="text" name="avatar_url" value="{{ avatar_url }}" required></div>
                        <div class="input-group"><label>Dashboard Background URL</label><i class="fa-solid fa-desktop"></i><input type="text" name="bg_url" value="{{ bg_url }}" required></div>
                        <button type="submit" class="btn" style="background: linear-gradient(135deg, #ffaa00, #ff6600);">Deploy Updates</button>
                    </form>
                </div>
            </div>
            {% endif %}

            <div class="footer-tag">BUILT BY <span>YATHIN</span> & <span>GOOGLE</span></div>
        </div>
    </div>
    <script>
        function switchTab(tabId) {
            document.querySelectorAll('.tab-section').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
        }
        setInterval(() => {
            if(document.getElementById('cpu-bar')) {
                let newCpu = Math.floor(Math.random() * 30) + 20;
                document.getElementById('cpu-bar').style.width = newCpu + '%';
                document.getElementById('cpu-val').innerText = newCpu + '%';
                let newRam = (1.2 + Math.random() * 0.5).toFixed(1);
                document.getElementById('ram-val').innerText = newRam + ' GB / 8.0 GB';
            }
        }, 3000);
    </script>
    {% endif %}
</body></html>
"""

@app.route('/')
def home():
    uptime = round((time.time() - start_time) / 3600, 2)
    return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in', False), role=session.get('role', 'admin'), error=session.pop('error', None), uptime=uptime, messages=bot_stats['messages_processed'], compressions=bot_stats['compressions_done'], avatar_url=ui_config['avatar_url'], bg_url=ui_config['bg_url'])

@app.route('/login', methods=['POST'])
def login():
    pw = request.form.get('password')
    if pw == ADMIN_PASSWORD: session['logged_in'], session['role'] = True, 'admin'
    elif pw == DEV_PASSWORD: session['logged_in'], session['role'] = True, 'dev'
    else: session['error'] = "ACCESS DENIED: Invalid Security Key."
    return redirect('/')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')

@app.route('/update_dev', methods=['POST'])
def update_dev():
    if session.get('role') == 'dev':
        ui_config['avatar_url'] = request.form.get('avatar_url', ui_config['avatar_url'])
        ui_config['bg_url'] = request.form.get('bg_url', ui_config['bg_url'])
    return redirect('/')

def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()