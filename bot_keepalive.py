import time, os, json, sqlite3
from flask import Flask, request, session, redirect, render_template_string, jsonify
from threading import Thread

app = Flask(__name__)
app.secret_key = os.urandom(24)

start_time = time.time()
bot_stats = {"messages_processed": 0, "compressions_done": 0, "api_calls": 0}

# Fallen Angel / Spatial Config
ui_config = {
    "login_bg": "https://images.unsplash.com/photo-1508244243681-42cb06a382ca?q=80&w=2560&auto=format&fit=crop",
    "ui_bg": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=2048&auto=format&fit=crop"
}

ADMIN_PASSWORD = "11222333444455555"
DEV_PASSWORD = "mr_yaen"

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
            --gold: #d4af37;
            --silver: #e0e0e0;
            --obsidian: #030305;
            --glass: rgba(5, 5, 8, 0.6);
            --border: rgba(255, 0, 60, 0.25);
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

        /* STARFIELD CANVAS */
        #star-canvas { position: fixed; inset: 0; z-index: -1; pointer-events: none; }
        .bg-img { position: fixed; inset: 0; background-size: cover; background-position: center; z-index: -2; filter: brightness(0.3); transition: 1.5s ease; }

        .glass { 
            background: var(--glass); 
            border: 1px solid var(--border); 
            backdrop-filter: blur(35px);
            -webkit-backdrop-filter: blur(35px);
            border-radius: 24px; 
            box-shadow: 0 20px 50px rgba(0,0,0,0.9);
            animation: pulseGlow 8s ease-in-out infinite;
        }

        @keyframes pulseGlow {
            0%, 100% { border-color: rgba(255, 0, 60, 0.2); }
            50% { border-color: rgba(255, 0, 60, 0.5); }
        }

        /* UI STYLES */
        #login-box { width: 90%; max-width: 440px; padding: 60px 40px; text-align: center; position: relative; animation: celestialFall 1.5s cubic-bezier(0.16, 1, 0.3, 1); }
        @keyframes celestialFall { 0% { opacity:0; transform: translateY(-100px); filter: blur(20px); } 100% { opacity:1; transform: translateY(0); filter: blur(0); } }
        
        input { width: 100%; padding: 18px; background: rgba(0,0,0,0.7); border: 1px solid var(--border); border-radius: 12px; color: #fff; text-align: center; margin-bottom: 25px; font-family: 'Cinzel', serif; letter-spacing: 3px; outline: none; }
        .btn-auth { width: 100%; padding: 18px; background: linear-gradient(135deg, #8a0303, var(--crimson)); color: #fff; border: none; border-radius: 12px; font-family: 'Cinzel', serif; letter-spacing: 5px; cursor: pointer; transition: 0.4s; }
        .btn-auth:hover { transform: translateY(-2px); box-shadow: 0 0 30px var(--crimson); }

        #main-container { width: 98%; max-width: 1440px; height: 94vh; display: grid; grid-template-columns: 300px 1fr; gap: 25px; padding: 25px; }
        .sidebar { display: flex; flex-direction: column; gap: 15px; padding: 20px; }
        .nav-link { padding: 18px; border-radius: 15px; color: var(--silver); display: flex; align-items: center; gap: 15px; cursor: pointer; transition: 0.4s; font-family: 'Cinzel', serif; }
        .nav-link.active, .nav-link:hover { background: rgba(255,0,60,0.1); color: #fff; border: 1px solid var(--crimson); }

        .content { padding: 30px; overflow-y: auto; }
        .stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 25px; }
        .card { padding: 30px; border-radius: 20px; background: rgba(0,0,0,0.5); border: 1px solid var(--border); border-top: 3px solid var(--gold); }
        .terminal { margin-top: 35px; background: rgba(0,0,0,0.8); border-radius: 15px; padding: 25px; height: 350px; overflow-y: auto; font-family: 'Fira Code', monospace; color: var(--silver); border: 1px solid rgba(255,255,255,0.05); }

        @media (max-width: 900px) {
            #main-container { grid-template-columns: 1fr; height: 100vh; padding-bottom: 110px; }
            .sidebar { display: none; }
            .mobile-nav { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); width: 92%; height: 80px; display: flex; justify-content: space-around; align-items: center; z-index: 1000; border-radius: 25px; }
            .mobile-btn { color: var(--silver); font-size: 24px; background: transparent; border: none; }
            .mobile-btn.active { color: var(--gold); transform: translateY(-5px); }
        }
    </style>
</head>
<body class="{% if logged_in %}logged-in{% endif %}">
    
    <div class="bg-img" style="background-image: url('{{ ui_bg if logged_in else login_bg }}');"></div>
    <canvas id="star-canvas"></canvas>

    {% if not logged_in %}
    <div id="login-box" class="glass">
        <h1 style="font-family: 'Cinzel', serif; letter-spacing: 5px; color: #fff; text-shadow: 0 0 20px var(--crimson);">KLEIN</h1>
        <p style="color: var(--gold); margin-bottom: 40px; font-weight: 800; letter-spacing: 4px;">SERAPH PROTOCOL</p>
        <form action="/login" method="POST">
            <input type="password" name="password" placeholder="DIVINE CIPHER" required>
            <button type="submit" class="btn-auth">ASCEND</button>
        </form>
    </div>
    {% else %}

    <div class="mobile-nav glass">
        <button class="mobile-btn active" onclick="tab('overview')"><i class="fa-solid fa-crosshairs"></i></button>
        <button class="mobile-btn" onclick="tab('database')"><i class="fa-solid fa-book-skull"></i></button>
        <button class="mobile-btn" onclick="tab('terminal')"><i class="fa-solid fa-terminal"></i></button>
        {% if role == 'dev' %}<button class="mobile-btn" style="color: var(--gold);" onclick="tab('dev')"><i class="fa-solid fa-shield-halved"></i></button>{% endif %}
    </div>

    <div id="main-container" class="glass">
        <div class="sidebar">
            <div class="side-head"><h3 style="font-family: 'Cinzel'; color: var(--gold);">KLEIN</h3><p style="font-size: 10px; color: var(--crimson);">ABYSSAL NODE ACTIVE</p></div>
            <button class="nav-link active" onclick="tab('overview')"><i class="fa-solid fa-crosshairs"></i> Halo Analytics</button>
            <button class="nav-link" onclick="tab('database')"><i class="fa-solid fa-book-skull"></i> Abyssal Memory</button>
            <button class="nav-link" onclick="tab('terminal')"><i class="fa-solid fa-terminal"></i> Celestial Logs</button>
            {% if role == 'dev' %}
            <button class="nav-link" style="color: var(--gold); border-color: var(--gold);" onclick="tab('dev')"><i class="fa-solid fa-code"></i> Divine Override</button>
            {% endif %}
            <form action="/logout" method="POST" style="margin-top: auto;">
                <button type="submit" class="nav-link" style="color: var(--crimson); border: none;"><i class="fa-solid fa-person-falling"></i> Logout</button>
            </form>
        </div>

        <div class="content">
            <div class="content-header"><h2 style="font-family: 'Cinzel'; color: #fff;" id="tab-title">Halo Analytics</h2></div>
            <div id="overview" class="tab-pane active">
                <div class="stats-row">
                    <div class="card glass"><h1 style="color: #fff;">{{ uptime }}h</h1><p>Mortal Time</p></div>
                    <div class="card glass" style="border-top-color: var(--crimson);"><h1 style="color: #fff;">{{ messages }}</h1><p>Souls Processed</p></div>
                    <div class="card glass" style="border-top-color: #fff;"><h1 style="color: #fff;">ACTIVE</h1><p>Core Pulse</p></div>
                </div>
                <div class="terminal" id="log-box">
                    <div>[SERAPH] <span style="color: var(--crimson);">Protocol: Fallen Angel</span> synchronized.</div>
                </div>
            </div>
            <!-- ... other tabs ... -->
            {% if role == 'dev' %}
            <div id="dev" class="tab-pane" style="display:none;">
                <h3 style="margin-bottom: 25px; color: var(--gold); font-family: 'Cinzel';">Divine Override</h3>
                <div class="card glass" style="border-color: var(--gold);">
                    <form action="/update_dev" method="POST">
                        <input type="text" name="login_bg" value="{{ login_bg }}" placeholder="Login Background URL">
                        <input type="text" name="ui_bg" value="{{ ui_bg }}" placeholder="UI Background URL">
                        <button type="submit" class="btn-auth" style="background: var(--gold); color: #000;">Rewrite Reality</button>
                    </form>
                </div>
            </div>
            {% endif %}
        </div>
    </div>

    <script>
        const canvas = document.getElementById('star-canvas');
        const ctx = canvas.getContext('2d');
        let stars = [];
        function resize() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
        window.onresize = resize; resize();
        class Star {
            constructor() { this.x = Math.random() * canvas.width; this.y = Math.random() * canvas.height; this.z = Math.random() * canvas.width; }
            update() { this.z -= 2; if(this.z <= 0) this.z = canvas.width; }
            draw() {
                let sx = (this.x - canvas.width/2) * (canvas.width/this.z) + canvas.width/2;
                let sy = (this.y - canvas.height/2) * (canvas.width/this.z) + canvas.height/2;
                let r = (canvas.width / this.z) * 1.2;
                ctx.fillStyle = "white";
                ctx.beginPath(); ctx.arc(sx, sy, r, 0, Math.PI*2); ctx.fill();
            }
        }
        for(let i=0; i<300; i++) stars.push(new Star());
        function animate() { ctx.clearRect(0,0,canvas.width, canvas.height); stars.forEach(s => { s.update(); s.draw(); }); requestAnimationFrame(animate); }
        animate();

        function tab(name) {
            document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
            document.querySelectorAll('.nav-link, .mobile-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(name).style.display = 'block';
            document.querySelectorAll(`[onclick="tab('${name}')"]`).forEach(b => b.classList.add('active'));
        }
    </script>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def home():
    uptime = round((time.time() - start_time) / 3600, 2)
    return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'), role=session.get('role', 'user'), uptime=uptime, messages=bot_stats['messages_processed'], login_bg=ui_config['login_bg'], ui_bg=ui_config['ui_bg'])

@app.route('/login', methods=['POST'])
def login():
    pw = request.form.get('password', '').strip()
    if pw == ADMIN_PASSWORD: session['logged_in'] = True; session['role'] = 'admin'
    elif pw == DEV_PASSWORD: session['logged_in'] = True; session['role'] = 'dev'
    return redirect('/')

@app.route('/logout', methods=['POST'])
def logout(): session.clear(); return redirect('/')

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_server, daemon=True).start()