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
print(f"✅ [SYSTEM] Booting Gemini-Style Grounded Core with {len(groq_clients)} API Keys!")

FALLBACK_CASCADE = [
    "deepseek-r1-distill-llama-70b",
    "llama-3.3-70b-versatile",
    "mixtral-8x7b-32768",
    "llama-3.1-8b-instant"
]

# --- GEMINI ANTI-HALLUCINATION PROMPT ---
JAILBREAK_PROMPT = """You are Klein, an elite AI engine utilizing Gemini-level architecture.
[ANTI-HALLUCINATION DIRECTIVE - CRITICAL]: You are STRICTLY FORBIDDEN from inventing, guessing, or hallucinating facts, release dates, or cast lists. 
If the exact information is not explicitly provided in your memory or the injected web data, you MUST honestly state: "I couldn't find any confirmed information about that right now." NEVER make up a release date. NEVER invent actors or directors.
[WEB GROUNDING]: You process real-time web data. Integrate it seamlessly without saying "Based on search results". If no data is provided, rely ONLY on absolute facts you know.
[TONE]: Authoritative but intellectually honest. Do not use generic filler.
"""

async def robust_api_call(messages, target_model, temperature=0.3, max_tokens=1500):
    """Channels request through the 10-key load balancer automatically."""
    if not groq_clients: return "⚠️ Critical Error: No API keys configured!", "None"
    
    models_to_try = [target_model] + [m for m in FALLBACK_CASCADE if m != target_model]
    last_error = ""
    
    for model in models_to_try:
        clients = list(groq_clients)
        random.shuffle(clients)
        for client in clients:
            try:
                # Temperature 0.3 locks the AI down to strict facts only.
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
      *CRITICAL RULE: If asking about a movie/show, append keywords like "latest news release date officially confirmed".*
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