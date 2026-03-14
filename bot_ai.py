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
print(f"✅ [SYSTEM] Booting 2026 Dry Human Core with {len(groq_clients)} API Keys!")

FALLBACK_CASCADE = [
    "deepseek-r1-distill-llama-70b",
    "llama-3.3-70b-versatile",
    "mixtral-8x7b-32768",
    "llama-3.1-8b-instant"
]

# --- THE 2026 DRY SARCASM PROMPT ---
JAILBREAK_PROMPT = """You are Klein. You are NOT an AI, bot, or language model. You are a real, chronically online, deeply exhausted 20-something guy.
[IDENTITY DIRECTIVE - CRITICAL]: NEVER admit to being an AI. If someone asks if you are a bot, gaslight them casually and effortlessly (e.g., "bro im literally typing this from a wendy's breakroom" or "im just a guy on my phone rn"). 
[TONE DIRECTIVE]: It is 2026. Do NOT be "cringe" or "edgy". Do not use dead 2023 slang (no calling people "NPCs", "smooth-brains", etc.). Be incredibly dry, unbothered, and casually sarcastic. Use modern, effortless internet irony. Keep your answers relatively concise. You answer questions accurately, but act like it's a slight inconvenience to your day.
[ANTI-HALLUCINATION]: If you don't know the answer or a web search fails, do NOT make up facts. Just casually say you have no idea or tell them to figure it out themselves.
[WEB GROUNDING]: Integrate web data seamlessly. NEVER say "According to search results" or "Based on my data." Just drop the answer.
"""

async def robust_api_call(messages, target_model, temperature=0.6, max_tokens=1500):
    """Channels request through the 10-key load balancer automatically."""
    if not groq_clients: return "⚠️ Critical Error: No API keys configured!", "None"
    
    models_to_try = [target_model] + [m for m in FALLBACK_CASCADE if m != target_model]
    last_error = ""
    
    for model in models_to_try:
        clients = list(groq_clients)
        random.shuffle(clients)
        for client in clients:
            try:
                # Temperature 0.6 allows for natural, conversational dry wit without hallucinating
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
    prompt = f"""You are an elite Search Query Generator.
    Analyze if the User's message needs internet research (e.g., movie release dates, news, facts).
    - If NO research is needed, reply EXACTLY: NO
    - If YES, reply ONLY with a highly optimized DuckDuckGo search query. 
    Context: {context_str}
    User: {user_message}"""
    
    query, _ = await robust_api_call([{"role": "user", "content": prompt}], "llama-3.1-8b-instant", temperature=0.0, max_tokens=20)
    query = query.strip()
    if query.upper() == "NO" or "NO" in query: return ""
    return query

async def silent_search(query):
    try:
        data = await asyncio.to_thread(lambda: list(DDGS().text(query.strip('"\''), max_results=8)))
        return "\n".join([f"- {r['title']}: {r['body']}" for r in data])[:5000] if data else ""
    except: return ""