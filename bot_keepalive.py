import time, os, json, sqlite3
from flask import Flask, request, session, redirect, render_template_string, jsonify
from threading import Thread

app = Flask(__name__)
app.secret_key = os.urandom(24)

start_time = time.time()
bot_stats = {"messages_processed": 0, "compressions_done": 0, "api_calls": 0}

# Fallen Angel & Spatial Themes
ui_config = {
    "avatar_url": "https://i.imgur.com/8Qz9f4u.png", # Abstract dark halo/core
    "login_bg": "https://images.unsplash.com/photo-1508244243681-42cb06a382ca?q=80&w=2560&auto=format&fit=crop", # Dark misty clouds
    "ui_bg": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=2048&auto=format&fit=crop" # Deep spatial nebula
}

ADMIN_PASSWORD = "11222333444455555"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Klein | Seraph Protocol</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Outfit:wght@300;400;700&family=Fira+Code&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --crimson: #ff003c;
            --blood: #8a0303;
            --gold: #d4af37;
            --silver: #e0e0e0;
            --obsidian: #050508;
            --glass-bg: rgba(5, 5, 8, 0.5);
            --glass-border: rgba(255, 0, 60, 0.3);
        }

        * { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color: transparent; }
        
        body { 
            background-color: var(--obsidian);
            color: var(--silver); 
            height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            overflow: hidden;
            font-family: 'Outfit', sans-serif;
        }

        h1, h2, h3 { font-family: 'Cinzel', serif; }

        /* LIVE BACKGROUNDS (CSS MOTION GRAPHICS) */
        .bg-layer { position: fixed; inset: 0; background-size: cover; background-position: center; z-index: -3; transition: opacity 1s; }
        .bg-login { background-image: url('{{ login_bg }}'); }
        .bg-ui { background-image: url('{{ ui_bg }}'); opacity: 0; }
        .logged-in .bg-login { opacity: 0; }
        .logged-in .bg-ui { opacity: 1; }

        /* SPATIAL DRIFT & ASH FALL ANIMATIONS */
        .particles { position: fixed; inset: 0; z-index: -2; pointer-events: none; }
        .logged-in .particles { animation: spatialDrift 60s linear infinite; background: radial-gradient(circle, transparent 20%, var(--obsidian) 120%), url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="0.5" fill="%23ffffff" opacity="0.3"/></svg>') repeat; background-size: 200px 200px; }
        @keyframes spatialDrift { 0% { background-position: 0 0; } 100% { background-position: 1000px 500px; } }

        /* LIQUID GLASS W/ OBSIDIAN TINT */
        .glass { 
            background: var(--glass-bg); 
            border: 1px solid var(--glass-border); 
            backdrop-filter: blur(25px); 
            -webkit-backdrop-filter: blur(25px);
            border-radius: 20px; 
            box-shadow: 0 15px 35px rgba(0,0,0,0.8), inset 0 0 20px rgba(255, 0, 60, 0.1);
        }

        /* LOGIN SCREEN - FALLEN ANGEL */
        #login-box { width: 90%; max-width: 420px; padding: 50px 40px; text-align: center; position: relative; animation: celestialDrop 1s cubic-bezier(0.2, 0.8, 0.2, 1); }
        @keyframes celestialDrop { from { opacity: 0; transform: translateY(-50px) scale(0.9); filter: blur(10px); } to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); } }
        
        .halo { position: absolute; top: -30px; left: 50%; transform: translateX(-50%); width: 100px; height: 10px; border-radius: 50%; border-top: 2px solid var(--gold); box-shadow: 0 -10px 20px var(--gold); opacity: 0.6; }
        
        input { width: 100%; padding: 18px; background: rgba(0,0,0,0.6); border: 1px solid var(--crimson); border-radius: 12px; color: #fff; font-size: 16px; outline: none; margin-bottom: 25px; text-align: center; letter-spacing: 3px; font-family: 'Cinzel', serif; transition: 0.3s; }
        input:focus { box-shadow: 0 0 25px rgba(255,0,60,0.4); background: rgba(255,0,60,0.05); }
        
        .btn-auth { width: 100%; padding: 18px; background: linear-gradient(135deg, var(--blood), var(--crimson)); color: #fff; border: none; border-radius: 12px; font-weight: 900; cursor: pointer; text-transform: uppercase; letter-spacing: 4px; box-shadow: 0 10px 30px rgba(255,0,60,0.3); font-family: 'Cinzel', serif; transition: 0.4s; position: relative; overflow: hidden; }
        .btn-auth::after { content: ''; position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent); transition: 0.5s; }
        .btn-auth:hover::after { left: 100%; }
        .btn-auth:hover { box-shadow: 0 0 40px var(--crimson); text-shadow: 0 0 10px #fff; }

        /* MAIN DASHBOARD (SPATIAL PC) */
        #main-container { width: 98%; max-width: 1400px; height: 94vh; display: grid; grid-template-columns: 280px 1fr; gap: 20px; padding: 20px; animation: fadeIn 1s; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        
        .sidebar { display: flex; flex-direction: column; gap: 15px; padding: 25px 20px; }
        .side-head { text-align: center; margin-bottom: 30px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 20px; }
        .side-head h3 { font-size: 28px; color: var(--gold); letter-spacing: 4px; text-shadow: 0 0 15px var(--gold); }
        .side-head p { color: var(--crimson); font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-top: 5px; }

        .nav-link { padding: 16px 20px; border-radius: 12px; background: transparent; color: var(--silver); border: 1px solid transparent; text-align: left; cursor: pointer; font-weight: 400; display: flex; align-items: center; gap: 15px; font-size: 15px; transition: 0.4s; font-family: 'Cinzel', serif; letter-spacing: 1px; }
        .nav-link.active, .nav-link:hover { background: rgba(255,0,60,0.1); color: #fff; border-color: var(--crimson); box-shadow: inset 0 0 15px rgba(255,0,60,0.2); text-shadow: 0 0 8px #fff; }

        .content { padding: 30px; overflow-y: auto; position: relative; }
        .content-header { margin-bottom: 40px; border-bottom: 1px solid rgba(255,0,60,0.3); padding-bottom: 15px; }
        .content-header h2 { font-size: 28px; letter-spacing: 3px; color: #fff; text-shadow: 0 0 15px var(--crimson); }

        .stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 25px; }
        .card { padding: 30px; border-radius: 15px; background: rgba(0,0,0,0.4); border-top: 1px solid var(--gold); position: relative; overflow: hidden; transition: 0.3s; }
        .card:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(212,175,55,0.1); }
        .card h1 { font-size: 45px; font-weight: 900; color: #fff; position: relative; z-index: 1; text-shadow: 0 2px 10px rgba(0,0,0,0.8); }
        .card p { font-size: 12px; color: var(--gold); font-weight: 700; text-transform: uppercase; letter-spacing: 2px; position: relative; z-index: 1; font-family: 'Outfit', sans-serif; }

        .terminal { margin-top: 35px; background: rgba(5,5,8,0.8); border-radius: 12px; padding: 25px; height: 320px; overflow-y: auto; font-family: 'Fira Code', monospace; font-size: 13px; color: var(--silver); border: 1px solid rgba(255,255,255,0.1); box-shadow: inset 0 0 30px rgba(0,0,0,1); }
        .t-red { color: var(--crimson); text-shadow: 0 0 5px var(--crimson); }
        .t-gold { color: var(--gold); }

        /* MOBILE OVERRIDES (Adaptive UI) */
        @media (max-width: 850px) {
            #main-container { grid-template-columns: 1fr; height: 100vh; width: 100%; border-radius: 0; padding: 15px; padding-bottom: 100px; border: none; }
            .sidebar { display: none; } 
            
            .mobile-nav { position: fixed; bottom: 25px; left: 50%; transform: translateX(-50%); width: 92%; height: 75px; display: flex; justify-content: space-around; align-items: center; z-index: 1000; padding: 0 10px; border-radius: 20px; border-color: var(--crimson); }
            .mobile-btn { color: var(--silver); font-size: 22px; background: transparent; border: none; transition: 0.4s; }
            .mobile-btn.active { color: var(--gold); text-shadow: 0 0 15px var(--gold); transform: translateY(-5px) scale(1.1); }
            
            .content { padding: 15px; }
            .card h1 { font-size: 36px; }
            .content-header h2 { font-size: 22px; }
            .terminal { height: 400px; }
        }
        @media (min-width: 851px) { .mobile-nav { display: none; } }
    </style>
</head>
<body class="{% if logged_in %}logged-in{% endif %}">
    
    <div class="bg-layer bg-login"></div>
    <div class="bg-layer bg-ui"></div>
    <div class="particles"></div>

    <!-- LOGIN SCREEN -->
    {% if not logged_in %}
    <div id="login-box" class="glass">
        <div class="halo"></div>
        <h1 style="letter-spacing: 5px; color: #fff; text-shadow: 0 0 20px var(--crimson); margin-bottom: 5px;">KLEIN</h1>
        <p style="color: var(--gold); margin-bottom: 40px; font-size: 12px; font-weight: 700; letter-spacing: 4px; font-family: 'Cinzel', serif;">Fallen Angel Protocol</p>
        <form action="/login" method="POST">
            <input type="password" name="password" placeholder="Divine Cipher" required>
            <button type="submit" class="btn-auth">Awaken</button>
        </form>
    </div>
    {% else %}

    <!-- MOBILE NAVIGATION -->
    <div class="mobile-nav glass">
        <button class="mobile-btn active" onclick="tab('overview')"><i class="fa-solid fa-crosshairs"></i></button>
        <button class="mobile-btn" onclick="tab('database')"><i class="fa-solid fa-book-skull"></i></button>
        <button class="mobile-btn" onclick="tab('terminal')"><i class="fa-solid fa-terminal"></i></button>
    </div>

    <!-- DASHBOARD -->
    <div id="main-container" class="glass">
        <!-- SIDEBAR -->
        <div class="sidebar">
            <div class="side-head">
                <h3>KLEIN</h3>
                <p>Abyssal Node Active</p>
            </div>
            <button class="nav-link active" onclick="tab('overview')"><i class="fa-solid fa-crosshairs"></i> Halo Analytics</button>
            <button class="nav-link" onclick="tab('database')"><i class="fa-solid fa-book-skull"></i> Abyssal Memory</button>
            <button class="nav-link" onclick="tab('terminal')"><i class="fa-solid fa-terminal"></i> Celestial Logs</button>
            <form action="/logout" method="POST" style="margin-top: auto;">
                <button type="submit" class="nav-link" style="color: var(--crimson); border-color: transparent;"><i class="fa-solid fa-person-falling"></i> Descend (Logout)</button>
            </form>
        </div>

        <!-- MAIN CONTENT AREA -->
        <div class="content">
            <div class="content-header">
                <h2 id="tab-title">Halo Analytics</h2>
            </div>

            <!-- OVERVIEW TAB -->
            <div id="overview" class="tab-pane active">
                <div class="stats-row">
                    <div class="card glass"><h1>{{ uptime }}h</h1><p>Mortal Time Elapsed</p></div>
                    <div class="card glass" style="border-top-color: var(--crimson);"><h1>{{ messages }}</h1><p>Souls Processed</p></div>
                    <div class="card glass" style="border-top-color: #fff;"><h1>FALLEN</h1><p>Core State</p></div>
                </div>
                <div class="terminal" id="log-box">
                    <div>[KLEIN-SYS] <span class="t-red">Protocol: Fallen Angel</span> initialized.</div>
                    <div>[KLEIN-SYS] Spatial distortion detected in local sector.</div>
                    <div>[SYSTEM] Binding dark matter to API nodes... Success.</div>
                </div>
            </div>

            <!-- DATABASE TAB -->
            <div id="database" class="tab-pane" style="display:none;">
                <h3 style="margin-bottom: 25px; color: var(--gold); font-family: 'Cinzel', serif;">Tome of Memory</h3>
                <div class="card glass" style="margin-bottom: 20px; border-color: var(--crimson);">
                    <p style="color: var(--silver);">Fragments Retained</p>
                    <h1 id="mem-count" style="color: var(--crimson); text-shadow: 0 0 15px var(--crimson);">Sealed</h1>
                </div>
            </div>

            <!-- TERMINAL TAB -->
            <div id="terminal" class="tab-pane" style="display:none;">
                <div class="terminal" style="height: 500px;" id="full-term">
                    <div>[ABYSS] Terminal access granted to Master.</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function tab(name) {
            document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
            document.querySelectorAll('.nav-link, .mobile-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(name).style.display = 'block';
            
            const titles = { 'overview': 'Halo Analytics', 'database': 'Abyssal Memory', 'terminal': 'Celestial Logs' };
            document.getElementById('tab-title').innerText = titles[name];
            
            const btns = document.querySelectorAll(`[onclick="tab('${name}')"]`);
            btns.forEach(b => b.classList.add('active'));
        }

        setInterval(() => {
            const lb = document.getElementById('log-box');
            if(Math.random() > 0.75 && lb) {
                const logs = ["[ABYSS] Fragmenting lost memory...", "[KLEIN] Celestial noise filtered.", "[CORE] Crimson limits holding stable.", "[NET] Divine uplink ping: 12ms"];
                lb.innerHTML += `<div>[${new Date().toLocaleTimeString()}] <span class="${Math.random() > 0.5 ? 't-red' : 't-gold'}">${logs[Math.floor(Math.random()*logs.length)]}</span></div>`;
                lb.scrollTop = lb.scrollHeight;
            }
        }, 3500);
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
        uptime=uptime, 
        messages=bot_stats['messages_processed'], 
        login_bg=ui_config['login_bg'], 
        ui_bg=ui_config['ui_bg'])

@app.route('/login', methods=['POST'])
def login():
    pw = request.form.get('password', '').strip()
    if pw == ADMIN_PASSWORD: session['logged_in'] = True
    return redirect('/')

@app.route('/logout', methods=['POST'])
def logout(): session.clear(); return redirect('/')

def run_server(): 
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive(): 
    Thread(target=run_server, daemon=True).start()