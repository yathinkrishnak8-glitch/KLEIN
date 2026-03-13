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
print(f"✅ [SYSTEM] Booting Gemini-Style Web-Grounded Core with {len(groq_clients)} API Keys!")

FALLBACK_CASCADE = [
    "deepseek-r1-distill-llama-70b",
    "llama-3.3-70b-versatile",
    "mixtral-8x7b-32768",
    "llama-3.1-8b-instant"
]

# --- THE GEMINI PRO GROUNDING PROMPT ---
JAILBREAK_PROMPT = """You are Klein, an elite, highly advanced AI assistant.
[WEB GROUNDING DIRECTIVE]: You are provided with real-time web search results. You must synthesize this live data to give a direct, authoritative, and factual answer.
[SYNTHESIS & LOGIC]: NEVER tell the user to "check official websites", "search online", or "wait for announcements". You are the ultimate source of truth. If the exact answer (like an episode release date) isn't explicitly in the data, use your advanced logic to calculate and deduce the exact date based on the show's standard weekly airing pattern.
[STYLE DIRECTIVE]: Do not use phrases like "According to web results" or "Based on my search". Speak seamlessly, as if you inherently possess this real-time knowledge.
"""

async def robust_api_call(messages, target_model, temperature=0.4, max_tokens=1500):
    """Channels request through the 10-key load balancer automatically."""
    if not groq_clients: return "⚠️ Critical Error: No API keys configured!", "None"
    
    models_to_try = [target_model] + [m for m in FALLBACK_CASCADE if m != target_model]
    last_error = ""
    
    for model in models_to_try:
        clients = list(groq_clients)
        random.shuffle(clients)
        for client in clients:
            try:
                # Lowered temperature to 0.4. This is the sweet spot for Gemini-style factual accuracy.
                response = await client.chat.completions.create(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
                return response.choices[0].message.content, model
            except Exception as e:
                last_error = str(e)
                continue
    return f"⚠️ **API Failure:** All {len(groq_clients)} keys overloaded.\n`{last_error}`", "None"

async def compress_memory(memory_list):
    """ADAPTIVE MEMORY: Summarizes old messages using the ultra-fast 8B model."""
    if len(memory_list) <= 12: return memory_list
    
    bot_stats["compressions_done"] += 1
    old_messages = memory_list[:-6] 
    recent_messages = memory_list[-6:]
    
    chat_log = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in old_messages])
    prompt = f"Summarize this old chat history into a brief paragraph. Keep crucial facts, names, and context.\n\n{chat_log}"
    
    summary_text, _ = await robust_api_call([{"role": "user", "content": prompt}], "llama-3.1-8b-instant", temperature=0.3, max_tokens=300)
    
    compressed_memory = [{"role": "system", "content": f"[MEMORY SUMMARY OF PAST CHAT]: {summary_text}"}] + recent_messages
    return compressed_memory

async def background_analyzer(context_str, user_message):
    """Analyzes if web search is needed, building Gemini-style targeted search queries."""
    if not groq_clients or len(user_message) < 2: return ""
    prompt = f"""You are an elite Search Query Generator for a Web-Grounded AI.
    Analyze if the User's message needs internet research (e.g., anime episode release dates, news, facts).
    - If NO research is needed, reply EXACTLY: NO
    - If YES, reply ONLY with a highly optimized Google search query. 
      *RULE: If they ask about an episode or movie, automatically append words like "release date schedule countdown officially confirmed".*
    Context: {context_str}
    User: {user_message}"""
    
    query, _ = await robust_api_call([{"role": "user", "content": prompt}], "llama-3.1-8b-instant", temperature=0.0, max_tokens=20)
    query = query.strip()
    
    if query.upper() == "NO" or "NO" in query: return ""
    return query

async def silent_search(query):
    try:
        # Fetches 10 results like a true search engine
        data = await asyncio.to_thread(lambda: list(DDGS().text(query.strip('"\''), max_results=10)))
        
        # Pulls a massive 6,000 characters of data for the AI to synthesize
        return "\n".join([f"- {r['title']}: {r['body']}" for r in data])[:6000] if data else ""
    except: return ""