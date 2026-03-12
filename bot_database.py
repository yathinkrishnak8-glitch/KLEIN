import sqlite3
import json

conn = sqlite3.connect('bot_database.db', check_same_thread=False, timeout=15.0)

DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TOGGLES = {
    "weather": True, "stats": True, "get_prompt": True, "personality": True, 
    "prank_idea": True, "setchannel": True, "unsetchannel": True, 
    "clearmemory": True, "changemodel": True, "snipe": True, "tldr": True, 
    "setdevlog": True, "info": True, "search": True, "news": True, 
    "deepdive": True, "auto_research": True, "target": True
}

def init_db():
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS server_config 
                      (guild_id TEXT PRIMARY KEY, toggles TEXT, personality TEXT, dev_channel TEXT, current_model TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS active_channels 
                      (channel_id TEXT PRIMARY KEY, guild_id TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_memory 
                      (channel_id TEXT PRIMARY KEY, history TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS snipes 
                      (channel_id TEXT PRIMARY KEY, data TEXT)''')
    conn.commit()

def get_config(guild_id):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT toggles, personality, dev_channel, current_model FROM server_config WHERE guild_id=?", (str(guild_id),))
        row = cursor.fetchone()
        if row: return json.loads(row[0]), row[1], row[2], row[3] or DEFAULT_MODEL
        return DEFAULT_TOGGLES.copy(), None, None, DEFAULT_MODEL
    except Exception:
        return DEFAULT_TOGGLES.copy(), None, None, DEFAULT_MODEL

def update_config(guild_id, toggles=None, personality=None, dev_channel=None, model=None):
    try:
        curr_t, curr_p, curr_d, curr_m = get_config(guild_id)
        t = json.dumps(toggles) if toggles else json.dumps(curr_t)
        p = personality if personality is not None else curr_p
        d = dev_channel if dev_channel is not None else curr_d
        m = model if model is not None else curr_m
        
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO server_config (guild_id, toggles, personality, dev_channel, current_model) VALUES (?, ?, ?, ?, ?)", 
                  (str(guild_id), t, p, d, m))
        conn.commit()
    except Exception: pass
