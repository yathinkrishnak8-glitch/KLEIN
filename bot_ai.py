import os, asyncio, random
from groq import AsyncGroq
from duckduckgo_search import DDGS
from bot_keepalive import bot_stats

raw_keys = os.getenv('GROQ_API_KEYS', os.getenv('GROQ_API_KEY', ''))
api_keys = [k.strip() for k in raw_keys.split(',') if k.strip()]
groq_clients = [AsyncGroq(api_key=key) for key in api_keys] if api_keys else []

FALLBACK_CASCADE = ["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b", "mixtral-8x7b-32768"]

async def robust_api_call(messages, target_model, temperature=0.6):
    if not groq_clients: return "⚠️ API Error.", "None"
    for model in [target_model] + FALLBACK_CASCADE:
        clients = list(groq_clients); random.shuffle(clients)
        for client in clients:
            try:
                resp = await client.chat.completions.create(model=model, messages=messages, temperature=temperature)
                return resp.choices[0].message.content, model
            except: continue
    return "⚠️ Overloaded.", "None"

async def background_analyzer(context, user_msg):
    prompt = f"Analyze if this needs research. If NO, reply 'NO'. If YES, reply ONLY with a query. site:wikipedia.org or site:fandom.com if applicable. Context: {context} | Msg: {user_msg}"
    query, _ = await robust_api_call([{"role": "user", "content": prompt}], "llama-3.1-8b-instant")
    return "" if "NO" in query.upper() else query.strip()

async def silent_search(query):
    try:
        data = await asyncio.to_thread(lambda: list(DDGS().text(query, max_results=5)))
        return "\n".join([f"- {r['body']}" for r in data])[:3000] if data else ""
    except: return ""