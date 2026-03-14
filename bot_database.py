import sqlite3
import json

conn = sqlite3.connect("klein_database.db", check_same_thread=False)

def init_db():
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS active_channels (channel_id TEXT PRIMARY KEY, guild_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chat_memory (channel_id TEXT PRIMARY KEY, history TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS server_configs (guild_id TEXT PRIMARY KEY, toggles TEXT, personality TEXT, max_history INTEGER, model TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS snipes (channel_id TEXT PRIMARY KEY, data TEXT)''')
    conn.commit()

def get_config(guild_id):
    c = conn.cursor()
    c.execute("SELECT toggles, personality, max_history, model FROM server_configs WHERE guild_id=?", (str(guild_id),))
    row = c.fetchone()
    if row:
        return json.loads(row[0]), row[1], row[2], row[3]
    # Defaults
    return {"auto_research": True}, "", 15, "llama-3.3-70b-versatile"

def update_config(guild_id, toggles=None, personality=None, max_history=None, model=None):
    current_toggles, current_pers, current_hist, current_model = get_config(guild_id)
    c = conn.cursor()
    c.execute("REPLACE INTO server_configs (guild_id, toggles, personality, max_history, model) VALUES (?, ?, ?, ?, ?)",
              (str(guild_id), 
               json.dumps(toggles) if toggles is not None else json.dumps(current_toggles),
               personality if personality is not None else current_pers,
               max_history if max_history is not None else current_hist,
               model if model is not None else current_model))
    conn.commit()