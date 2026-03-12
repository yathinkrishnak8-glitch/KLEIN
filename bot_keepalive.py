import time
from flask import Flask
from threading import Thread
import os

app = Flask('')
start_time = time.time()
bot_stats = {"messages_processed": 0}

@app.route('/')
def home():
    uptime = round((time.time() - start_time) / 3600, 2)
    return f"Modular Groq Core Online | msgs: {bot_stats['messages_processed']} | Uptime: {uptime}h"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()


