import os
import asyncio
import random
from groq import AsyncGroq
from duckduckgo_search import DDGS
from bot_keepalive import bot_stats

# --- 10-KEY LOAD BALANCER ---
raw_keys = os.getenv('GROQ_API_KEYS', os.getenv('GROQ_API_KEY', ''))
api_keys = [k.strip() for k in raw_keys.split(',') if k.strip()]

groq_clients = [AsyncGroq(api_key=key) for key in api_keys] if api_keys else []
print(f"✅ [SYSTEM] Booting Dynamic Omni-Core with {len(groq_clients)} API Keys!")

FALLBACK_CASCADE = [
    "deepseek-r1-distill-llama-70b",
    "llama-3.3-70b-versatile",
    "mixtral-8x7b-32768",
    "llama-3.1-8b-instant"
]

# --- NEUTRAL BASE SYSTEM (No forced personality) ---
BASE_SYSTEM = """
[SYSTEM DIRECTIVE]: You are an advanced AI assistant. 
[WEB GROUNDING]: Integrate scraped web data seamlessly into your answers. Do NOT say "According to search results."
[ANTI-HALLUCINATION]: If you do not know the answer, state clearly that you do not have that information. Do not invent facts.
"""

async def robust_api_call(messages, target_model, temperature=0.6, max_tokens=1500):
    if not groq_clients: return "⚠️ Critical Error: No API keys configured!", "None"
    
    models_to_try = [target_model] + [m for m in FALLBACK_CASCADE if m != target_model]
    last_error = ""
    
    for model in models_to_try:
        clients = list(groq_clients)
        random.shuffle(clients)
        for client in clients:
            try:
                response = await client.chat.completions.create(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
                return response.choices[0].message.content, model
            except Exception as e:
                last_error = str(e)
                continue
    return f"⚠️ **API Failure:** All {len(groq_clients)} keys overloaded.\n`{last_error}`", "None"

async def compress_memory(memory_list):
    if len(memory_list) <= 12: return memory_list
    bot_stats["compressions_done"] += 1
    old_messages = memory_list[:-6] 
    recent_messages = memory_list[-6:]
    chat_log = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in old_messages])
    prompt = f"Summarize this old chat history into a brief paragraph. Keep crucial facts, names, and context.\n\n{chat_log}"
    summary_text, _ = await robust_api_call([{"role": "user", "content": prompt}], "llama-3.1-8b-instant", temperature=0.3, max_tokens=300)
    return [{"role": "system", "content": f"[MEMORY SUMMARY OF PAST CHAT]: {summary_text}"}] + recent_messages

async def background_analyzer(context_str, user_message):
    if not groq_clients or len(user_message) < 2: return ""
    
    # The Elite OSINT Prompt
    prompt = f"""You are an elite Knowledge Retrieval Agent.
    Analyze if the User's message needs factual internet research.
    - If NO research is needed, reply EXACTLY: NO
    - If YES, reply ONLY with a highly optimized search query. 
    
    [STRICT SEARCH TACTICS]: 
    1. If the user asks about general history, science, or facts, append 'site:wikipedia.org' to the query.
    2. If the user asks about movies, cast, or anime watch orders, append 'site:imdb.com' or 'site:myanimelist.net'.
    3. If the user asks about game stats, weapon lore, or specific shows, append 'site:fandom.com'.
    
    Context: {context_str}
    User: {user_message}"""
    
    query, _ = await robust_api_call([{"role": "user", "content": prompt}], "llama-3.1-8b-instant", temperature=0.0, max_tokens=30)
    query = query.strip()
    
    if query.upper() == "NO" or "NO" in query: return ""
    
    print(f"🔍 [SCRAPER ACTIVE] Targeting Knowledge Base: {query}")
    return query

async def silent_search(query):
    try:
        data = await asyncio.to_thread(lambda: list(DDGS().text(query.strip('"\''), max_results=8)))
        return "\n".join([f"- {r['title']}: {r['body']}" for r in data])[:5000] if data else ""
    except: return ""