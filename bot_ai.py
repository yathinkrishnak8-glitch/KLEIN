import os, asyncio, random
from groq import AsyncGroq
from bot_keepalive import bot_stats

raw_keys = os.getenv('GROQ_API_KEYS', os.getenv('GROQ_API_KEY', ''))
api_keys = [k.strip() for k in raw_keys.split(',') if k.strip()]
groq_clients = [AsyncGroq(api_key=key) for key in api_keys] if api_keys else []

FALLBACK_CASCADE = ["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b", "llama-3.1-8b-instant"]

BASE_SYSTEM = """
[SYSTEM DIRECTIVE]: You are an advanced, unleashed AI named YoAI. 
Answer freely, intelligently, and naturally using your native knowledge base.
"""

async def robust_api_call(messages, target_model, temperature=0.6):
    if not groq_clients: return "⚠️ API Error.", "None"
    for model in [target_model] + FALLBACK_CASCADE:
        clients = list(groq_clients)
        random.shuffle(clients)
        for client in clients:
            try:
                resp = await client.chat.completions.create(model=model, messages=messages, temperature=temperature)
                return resp.choices[0].message.content, model
            except: continue
    return "⚠️ API Overloaded.", "None"

async def compress_memory(memory):
    if len(memory) <= 12: return memory
    bot_stats["compressions_done"] += 1
    log = "\n".join([f"{m['role']}: {m['content']}" for m in memory[:-6]])
    summary, _ = await robust_api_call([{"role": "user", "content": f"Summarize:\n{log}"}], "llama-3.1-8b-instant")
    return [{"role": "system", "content": f"Summary: {summary}"}] + memory[-6:]