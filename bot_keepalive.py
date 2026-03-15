import time, os, json, sqlite3
from flask import Flask, request, session, redirect, render_template_string, jsonify
from threading import Thread

app = Flask(__name__)
app.secret_key = os.urandom(24)

start_time = time.time()
bot_stats = {"messages_processed": 0, "compressions_done": 0, "api_calls": 0}

ui_config = {
    "avatar_url": "https://i.imgur.com/8Qz9f4u.png",
    "bg_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop",
    "bot_status": "Bypassing Mainframes..."
}

ADMIN_PASSWORD = "klein2026"
DEV_PASSWORD = "mr_yaen"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Klein | Omni-Core Apex</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800;900&family=Fira+Code&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --p: #00f0ff;
            --p-glow: rgba(0, 240, 255, 0.4);
            --bg: #050b14;
            --g: rgba(15, 23, 42, 0.6);
            --b: rgba(255, 255, 255, 0.1);
            --t: #ffffff;
            --tm: #8ab4f8;
            --danger: #ff3366;
        }

        [data-theme="light"] {
            --p: #0066ff;
            --p-glow: rgba(0, 102, 255, 0.2);
            --bg: #f3f4f6;
            --g: rgba(255, 255, 255, 0.8);
            --b: rgba(0, 0, 0, 0.1);
            --t: #111827;
            --tm: #4b5563;
        }

        * { margin:0; padding:0; box-sizing:border-box; font-family:'Outfit', sans-serif; -webkit-tap-highlight-color: transparent; }
        
        body { 
            background: var(--bg) url('{{ bg_url }}') center/cover fixed; 
            color: var(--t); 
            height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            overflow: hidden;
        }

        .blur-layer { position: fixed; inset: 0; backdrop-filter: blur(15px) brightness(0.6); z-index: -1; }

        .glass { 
            background: var(--g); 
            border: 1px solid var(--b); 
            backdrop-filter: blur(25px); 
            -webkit-backdrop-filter: blur(25px);
            border-radius: 30px; 
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        }

        /* LOGIN STYLES */
        #login-box { width: 90%; max-width: 400px; padding: 40px; text-align: center; animation: slideUp 0.6s ease; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        
        .bot-img { width: 110px; height: 110px; border-radius: 50%; border: 3px solid var(--p); box-shadow: 0 0 20px var(--p-glow); margin-bottom: 20px; }
        input { width: 100%; padding: 18px; background: rgba(0,0,0,0.2); border: 1px solid var(--b); border-radius: 15px; color: #fff; font-size: 16px; outline: none; margin-bottom: 15px; text-align: center; }
        input:focus { border-color: var(--p); box-shadow: 0 0 15px var(--p-glow); }
        .btn-auth { width: 100%; padding: 18px; background: var(--p); color: #000; border: none; border-radius: 15px; font-weight: 800; cursor: pointer; text-transform: uppercase; letter-spacing: 1px; }

        /* MAIN DASHBOARD (PC) */
        #main-container { 
            width: 98%; 
            max-width: 1400px; 
            height: 94vh; 
            display: grid; 
            grid-template-columns: 280px 1fr; 
            gap: 20px; 
            padding: 20px;
        }

        .sidebar { display: flex; flex-direction: column; gap: 10px; padding: 20px; }
        .side-head { text-align: center; margin-bottom: 30px; }
        .side-head img { width: 70px; border-radius: 50%; border: 2px solid var(--p); }

        .nav-link { 
            padding: 16px 20px; 
            border-radius: 16px; 
            background: transparent; 
            color: var(--tm); 
            border: none; 
            text-align: left; 
            cursor: pointer; 
            font-weight: 700; 
            display: flex; 
            align-items: center; 
            gap: 15px;
            font-size: 16px;
        }
        .nav-link.active, .nav-link:hover { background: var(--b); color: var(--p); }

        .content { padding: 30px; overflow-y: auto; position: relative; }
        .content-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }

        .stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; }
        .card { padding: 25px; border-radius: 20px; background: rgba(0,0,0,0.1); border-left: 4px solid var(--p); position: relative; }
        .card h1 { font-size: 36px; font-weight: 900; color: var(--t); }
        .card p { font-size: 12px; color: var(--tm); font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }

        .terminal { 
            margin-top: 30px; 
            background: #000; 
            border-radius: 15px; 
            padding: 20px; 
            height: 350px; 
            overflow-y: auto; 
            font-family: 'Fira Code', monospace; 
            font-size: 13px; 
            color: #00ffaa; 
            border: 1px solid var(--b);
        }

        /* MOBILE OVERRIDES (The magic bit) */
        @media (max-width: 850px) {
            #main-container { grid-template-columns: 1fr; height: 100vh; width: 100%; border-radius: 0; padding: 15px; padding-bottom: 90px; }
            .sidebar { display: none; } /* Hide PC sidebar */
            
            /* Bottom Mobile Nav */
            .mobile-nav {
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                width: 90%;
                height: 70px;
                display: flex;
                justify-content: space-around;
                align-items: center;
                z-index: 1000;
                padding: 0 10px;
            }
            .mobile-btn { color: var(--tm); font-size: 24px; background: transparent; border: none; }
            .mobile-btn.active { color: var(--p); }
            
            .content { padding: 10px; }
            .card h1 { font-size: 28px; }
            .content-header h2 { font-size: 24px; }
        }

        /* Hidden on PC, shown on Mobile Nav */
        @media (min-width: 851px) { .mobile-nav { display: none; } }

        .theme-ico { font-size: 24px; cursor: pointer; color: var(--p); }
        .toast { position: fixed; top: 20px; right: 20px; padding: 15px 25px; border-radius: 12px; background: var(--p); color: #000; font-weight: 800; transform: translateX(200%); transition: 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); z-index: 2000; }
        .toast.show { transform: translateX(0); }
    </style>
</head>
<body>
    <div class="blur-layer"></div>

    <!-- LOGIN SCREEN -->
    {% if not logged_in %}
    <div id="login-box" class="glass">
        <img src="{{ avatar_url }}" class="bot-img">
        <h1 style="letter-spacing: 3px; font-weight: 900;">OMNI-CORE</h1>
        <p style="color: var(--tm); margin-bottom: 30px; font-size: 14px;">Establish Authorized Uplink</p>
        <form action="/login" method="POST">
            <input type="password" name="password" placeholder="Access Key" required>
            <button type="submit" class="btn-auth">Initialize</button>
        </form>
        {% if error %}<p style="color: var(--danger); margin-top: 15px; font-weight: 800;">{{ error }}</p>{% endif %}
    </div>
    {% else %}

    <!-- MOBILE NAVIGATION (Hidden on PC) -->
    <div class="mobile-nav glass">
        <button class="mobile-btn active" onclick="tab('overview')"><i class="fa-solid fa-house"></i></button>
        <button class="mobile-btn" onclick="tab('database')"><i class="fa-solid fa-database"></i></button>
        <button class="mobile-btn" onclick="tab('terminal')"><i class="fa-solid fa-terminal"></i></button>
        {% if role == 'dev' %}
        <button class="mobile-btn" style="color: #ffaa00;" onclick="tab('dev')"><i class="fa-solid fa-shield"></i></button>
        {% endif %}
    </div>

    <!-- DASHBOARD (Grid Layout) -->
    <div id="main-container" class="glass">
        <!-- SIDEBAR (Hidden on Mobile) -->
        <div class="sidebar">
            <div class="side-head">
                <img src="{{ avatar_url }}">
                <h3 style="margin-top: 10px; letter-spacing: 1px;">KLEIN CORE</h3>
                <p style="color: #00ffaa; font-size: 11px; font-weight: 900;">UPLINK SECURE</p>
            </div>
            <button class="nav-link active" onclick="tab('overview')"><i class="fa-solid fa-house"></i> Home</button>
            <button class="nav-link" onclick="tab('database')"><i class="fa-solid fa-database"></i> Database</button>
            <button class="nav-link" onclick="tab('terminal')"><i class="fa-solid fa-terminal"></i> Terminal</button>
            {% if role == 'dev' %}
            <button class="nav-link" style="color: #ffaa00;" onclick="tab('dev')"><i class="fa-solid fa-code"></i> Developer</button>
            {% endif %}
            <form action="/logout" method="POST" style="margin-top: auto;">
                <button type="submit" class="nav-link" style="color: var(--danger);"><i class="fa-solid fa-power-off"></i> Disconnect</button>
            </form>
        </div>

        <!-- MAIN CONTENT AREA -->
        <div class="content">
            <div class="content-header">
                <h2 id="tab-title">System Analytics</h2>
                <div class="theme-ico" onclick="toggleTheme()"><i class="fa-solid fa-moon"></i></div>
            </div>

            <!-- OVERVIEW TAB -->
            <div id="overview" class="tab-pane active">
                <div class="stats-row">
                    <div class="card glass"><h1>{{ uptime }}h</h1><p>Core Uptime</p></div>
                    <div class="card glass"><h1>{{ messages }}</h1><p>AI Queries</p></div>
                    <div class="card glass" style="border-color: #a855f7;"><h1>10/10</h1><p>Active Groq Keys</p></div>
                </div>
                <div class="terminal" id="log-box">
                    <div>[SYSTEM] Booting Liquid Interface V6...</div>
                    <div>[SYSTEM] Adaptive layout established for PC and Mobile.</div>
                </div>
            </div>

            <!-- DATABASE TAB -->
            <div id="database" class="tab-pane" style="display:none;">
                <h3 style="margin-bottom: 20px;">Memory Management</h3>
                <div class="card glass" style="margin-bottom: 20px;">
                    <p>Current session storage</p>
                    <h1 id="mem-count">--</h1>
                </div>
                <button class="btn-auth" style="background: var(--danger); width: auto; padding: 15px 30px;" onclick="showToast('Memory Flush Triggered')">Flush Global Memory</button>
            </div>

            <!-- TERMINAL TAB -->
            <div id="terminal" class="tab-pane" style="display:none;">
                <div class="terminal" style="height: 500px;" id="full-term">
                    <div>[SHELL] Root access granted.</div>
                </div>
            </div>

            <!-- DEV TAB -->
            {% if role == 'dev' %}
            <div id="dev" class="tab-pane" style="display:none;">
                <h3 style="margin-bottom: 20px; color: #ffaa00;">Master Configuration</h3>
                <form action="/update_dev" method="POST">
                    <input type="text" name="avatar_url" value="{{ avatar_url }}" placeholder="Bot Avatar URL">
                    <input type="text" name="bg_url" value="{{ bg_url }}" placeholder="Background URL">
                    <button type="submit" class="btn-auth" style="background: #ffaa00;">Deploy Config</button>
                </form>
            </div>
            {% endif %}
        </div>
    </div>

    <div id="toast-msg" class="toast">Action Successful</div>

    <script>
        function tab(name) {
            document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
            document.querySelectorAll('.nav-link, .mobile-btn').forEach(b => b.classList.remove('active'));
            
            document.getElementById(name).style.display = 'block';
            document.getElementById('tab-title').innerText = name.charAt(0).toUpperCase() + name.slice(1);
            
            // Highlight active buttons on both Navs
            const btns = document.querySelectorAll(`[onclick="tab('${name}')"]`);
            btns.forEach(b => b.classList.add('active'));
        }

        function toggleTheme() {
            const h = document.documentElement;
            const t = h.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            h.setAttribute('data-theme', t);
            document.querySelector('.theme-ico i').className = t === 'dark' ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
        }

        function showToast(msg) {
            const t = document.getElementById('toast-msg');
            t.innerText = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 3000);
        }

        // Live Log Simulation
        setInterval(() => {
            const lb = document.getElementById('log-box');
            if(Math.random() > 0.8 && lb) {
                const logs = ["[API] Load balance: Key-3", "[MEM] Compressing sectors...", "[SYS] Heartbeat stable"];
                lb.innerHTML += `<div>[${new Date().toLocaleTimeString()}] ${logs[Math.floor(Math.random()*logs.length)]}</div>`;
                lb.scrollTop = lb.scrollHeight;
            }
        }, 4000);
    </script>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def home():
    uptime = round((time.time() - start_time) / 3600, 2)
    return render_template_string(HTML_TEMPLATE, 
        logged_in=session.get('logged_in'), 
        role=session.get('role', 'admin'), 
        error=session.pop('error', None), 
        uptime=uptime, 
        messages=bot_stats['messages_processed'], 
        avatar_url=ui_config['avatar_url'], 
        bg_url=ui_config['bg_url'])

@app.route('/login', methods=['POST'])
def login():
    pw = request.form.get('password', '').strip()
    if pw == ADMIN_PASSWORD: session['logged_in'], session['role'] = True, 'admin'
    elif pw == DEV_PASSWORD: session['logged_in'], session['role'] = True, 'dev'
    else: session['error'] = "INVALID KEY"
    return redirect('/')

@app.route('/logout', methods=['POST'])
def logout(): session.clear(); return redirect('/')

@app.route('/update_dev', methods=['POST'])
def update_dev():
    if session.get('role') == 'dev':
        ui_config['avatar_url'] = request.form.get('avatar_url', ui_config['avatar_url']).strip()
        ui_config['bg_url'] = request.form.get('bg_url', ui_config['bg_url']).strip()
    return redirect('/')

def run_server(): app.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run_server, daemon=True).start()