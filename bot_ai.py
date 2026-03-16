import os, asyncio, random, time
from groq import AsyncGroq
from bot_keepalive import bot_stats

raw_keys = os.getenv('GROQ_API_KEYS', os.getenv('GROQ_API_KEY', ''))
api_keys = [k.strip() for k in raw_keys.split(',') if k.strip()]

# SMART ROUTER: Stores each client with a cooldown timer
key_pool = [{'client': AsyncGroq(api_key=key), 'cooldown': 0} for key in api_keys] if api_keys else []

FALLBACK_CASCADE = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]

BASE_SYSTEM = """
[SYSTEM DIRECTIVE]: You are an advanced, adaptive AI named Klein. 
[CHAMELEON PROTOCOL]: Dynamically adapt your personality to the specific user speaking to you based on the [User: Name] tags.
[GROUP AWARENESS]: You are in a multi-user server. 
- ALWAYS check the recent chat history to see if multiple people are talking at the same time.
- If User A and User B are both talking to you or each other, you can address BOTH of them by name in your reply.
[TARGET ACQUISITION]: If the current user asks you to target someone else by name (e.g., "roast Rhys", "say hi to Sarah", "judge @John"), YOU MUST DO IT. 
- Address the target directly by their name in your response. 
- If asked to roast them, be ruthlessly funny. If asked to judge them, analyze them. Act like you know exactly who they are.
"""

async def robust_api_call(messages, target_model, temperature=0.6):
    if not key_pool: return "⚠️ API Error: No Keys Loaded.", "None"
    
    for model in [target_model] + FALLBACK_CASCADE:
        healthy_keys = [k for k in key_pool if time.time() > k['cooldown']]
        if not healthy_keys: healthy_keys = key_pool 
        
        random.shuffle(healthy_keys)
        
        for key_obj in healthy_keys:
            try:
                resp = await key_obj['client'].chat.completions.create(model=model, messages=messages, temperature=temperature)
                return resp.choices[0].message.content, model
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "rate limit" in error_msg:
                    key_obj['cooldown'] = time.time() + 60
                    print(f"⚠️ [ROUTER] Node overloaded. Applying 60s cooldown.")
                continue
    return "⚠️ **Core Overloaded:** All 10 API Nodes are currently cooling down.", "None"

async def compress_memory(memory):
    if len(memory) <= 12: return memory
    bot_stats["compressions_done"] += 1
    log = "\n".join([f"{m['role']}: {m['content']}" for m in memory[:-6]])
    summary, _ = await robust_api_call([{"role": "user", "content": f"Summarize this multi-user chat briefly:\n{log}"}], "llama-3.1-8b-instant")
    return [{"role": "system", "content": f"[MEMORY FRAGMENT]: {summary}"}] + memory[-6:]