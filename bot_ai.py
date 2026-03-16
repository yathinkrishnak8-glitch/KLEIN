            embed.timestamp = datetime.utcnow()
            await channel.send(embed=embed)

# --- KEEP-ALIVE SERVER ---
app = Flask('')
@app.route('/')
def home():
    uptime = round((time.time() - bot_stats["start_time"]) / 3600, 2)
    return f"V3.0 Autonomous Core Online | Processed {bot_stats['messages_processed']} msgs | Uptime: {uptime}h"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()

# --- DISCORD CLIENT ---
class GroqBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True 
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        self.status_task.start() 
        print(f"Logged in as {self.user} | V3.0 Autonomous Active")

    @tasks.loop(minutes=15)
    async def status_task(self):
        statuses = [
            discord.Activity(type=discord.ActivityType.watching, name="the Rumbling approach"),
            discord.Game(name="Free Fire Max on a Redmi"),
            discord.Activity(type=discord.ActivityType.listening, name="the Hellsing OST"),
            discord.Game(name="Blox Fruits"),
            discord.Activity(type=discord.ActivityType.playing, name="with the philosophy of weapons"),
            discord.Game(name="with LLaMA 3.3"),
            discord.Activity(type=discord.ActivityType.watching, name="over the network")
        ]
        await self.change_presence(activity=random.choice(statuses))

    @status_task.before_loop
    async def before_status_task(self):
        await self.wait_until_ready()

bot = GroqBot()

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    err_msg = f"❌ **Command Failed:** A system error occurred."
    try:
        if interaction.response.is_done(): await interaction.followup.send(err_msg, ephemeral=True)
        else: await interaction.response.send_message(err_msg, ephemeral=True)
    except: pass
    await send_dev_log(interaction.guild_id, str(error))

# ==========================================
# 🛑 THE BOUNCER: MASTER SWITCHBOARD
# ==========================================
@bot.tree.interaction_check
async def check_toggles(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.application_command:
        cmd_name = interaction.command.name
        guild_id = interaction.guild_id or interaction.user.id
        
        if cmd_name in ["toggle", "purge", "lockdown", "unlock"]: return True
            
        toggles, _, _ = get_config(guild_id)
        if cmd_name in toggles and not toggles[cmd_name]:
            await interaction.response.send_message(f"🔴 Access Denied. `/{cmd_name}` is disabled.", ephemeral=True)
            return False
    return True

@bot.tree.command(name="toggle", description="[ADMIN] Turn any bot command ON or OFF")
@app_commands.default_permissions(administrator=True)
async def toggle_cmd(interaction: discord.Interaction, command_name: str):
    await interaction.response.defer()
    cmd = command_name.lower()
    guild_id = interaction.guild_id or interaction.user.id
    toggles, _, _ = get_config(guild_id)
    
    if cmd not in toggles:
        return await interaction.followup.send(f"⚠️ I couldn't find a command named `{cmd}`.")
        
    toggles[cmd] = not toggles[cmd]
    update_config(guild_id, toggles=toggles)
    status = "🟢 **ENABLED**" if toggles[cmd] else "🔴 **DISABLED**"
    await interaction.followup.send(f"Master Switch: `{cmd}` is now {status}.")

# ==========================================
# 🌐 THE SCRAPER & NEWS ENGINE
# ==========================================
@bot.tree.command(name="search", description="Scrape the live internet and pull YouTube links")
async def search(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    def perform_scrape():
        try:
            text_res = list(DDGS().text(query, max_results=3))
            vid_res = list(DDGS().videos(query, max_results=1))
            return text_res, vid_res
        except: return [], []

    text_data, video_data = await asyncio.to_thread(perform_scrape)
    if not text_data: return await interaction.followup.send("❌ The web scraper couldn't extract any live data.")

    web_context = "\n".join([f"- {r['title']}: {r['body']}" for r in text_data])
    vid_link = video_data[0]['content'] if video_data else ""
    
    prompt = f"User Query: {query}\n\nLive Web Data:\n{web_context}\n\nAnswer the user naturally using this new data."
    response = await groq_client.chat.completions.create(model=bot_settings["primary_model"], messages=[{"role": "user", "content": prompt}], temperature=0.5)
    
    reply = f"🌐 **Live Web Search:** `{query}`\n\n{response.choices[0].message.content}"
    if vid_link: reply += f"\n\n📺 **Relevant Video:** {vid_link}"
    await interaction.followup.send(reply)

@bot.tree.command(name="news", description="Pull live news headlines based on a specific genre")
@app_commands.choices(genre=[
    app_commands.Choice(name="Anime & Manga", value="anime manga news"),
    app_commands.Choice(name="Mobile & PC Gaming", value="video game mobile gaming news"),
    app_commands.Choice(name="Technology & AI", value="technology artificial intelligence news"),
    app_commands.Choice(name="Global World News", value="global world news top stories")
])
async def news(interaction: discord.Interaction, genre: app_commands.Choice[str]):
    await interaction.response.defer()
    def scrape_news():
        try: return list(DDGS().news(genre.value, max_results=4))
        except: return []

    news_data = await asyncio.to_thread(scrape_news)
    if not news_data: return await interaction.followup.send("❌ The news satellite is currently unreachable.")

    embed = discord.Embed(title=f"📰 Latest {genre.name} Headlines", color=0xFF5500)
    for article in news_data:
        source = article.get('source', 'Unknown Source')
        embed.add_field(name=article['title'], value=f"[{source}]({article['url']})", inline=False)
    
    embed.set_footer(text="Live data pulled directly from the web.")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="deepdive", description="[PRO FEATURE] AI autonomously researches and writes a complex report")
async def deepdive(interaction: discord.Interaction, topic: str):
    await interaction.response.defer()
    await interaction.followup.send(f"⏳ *Initializing deep-dive protocols for `{topic}`. Scraping the web...*")
    
    def heavy_scrape():
        try: return list(DDGS().text(topic, max_results=6))
        except: return []

    raw_data = await asyncio.to_thread(heavy_scrape)
    if not raw_data: return await interaction.channel.send("❌ Scraper failed to retrieve data for the deep dive.")

    web_context = "\n\n".join([f"DATA POINT: {r['body']}" for r in raw_data])
    system_prompt = "You are Klein, an expert researcher. Synthesize the provided raw web data into a highly structured, brilliant, and comprehensive report. Use bolding, bullet points, and headers."
    
    response = await groq_client.chat.completions.create(
        model=bot_settings["primary_model"],
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Topic: {topic}\n\nRAW DATA:\n{web_context}"}],
        temperature=0.4
    )
    
    reply = response.choices[0].message.content
    if len(reply) > 2000:
        chunks = [reply[i:i+1995] for i in range(0, len(reply), 1995)]
        for chunk in chunks: await interaction.channel.send(chunk)
    else: await interaction.channel.send(reply)

# ==========================================
# ⚙️ SYSTEM & DEV TOOLS
# ==========================================
@bot.tree.command(name="info", description="View digital system status")
async def info(interaction: discord.Interaction):
    await interaction.response.defer()
    ping = round(bot.latency * 1000)
    uptime_hrs = round((time.time() - bot_stats["start_time"]) / 3600, 2)
    members = interaction.guild.member_count if interaction.guild else "N/A"
    _, current_personality, _ = get_config(interaction.guild_id or interaction.user.id)
    active_persona = current_personality if current_personality else "Default AI (Klein)"
    
    embed = discord.Embed(title="💠 SYSTEM TERMINAL :: V3.0", color=0x00FFFF)
    embed.add_field(name="📡 Status", value=f"🟢 Online\n**Ping:** `{ping}ms`\n**Uptime:** `{uptime_hrs}h`", inline=True)
    embed.add_field(name="👥 Network", value=f"**Members:** `{members}`\n**Messages:** `{bot_stats['messages_processed']}`", inline=True)
    embed.add_field(name="🧠 Active Core", value=f"**Model:** `{bot_settings['primary_model']}`", inline=False)
    embed.add_field(name="🎭 Current Personality", value=f"> *{active_persona}*", inline=False)
    embed.set_footer(text="⚙️ Built by yathin | Autonomous Engine Active")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="setdevlog", description="[ADMIN] Set channel for error logs")
@app_commands.default_permissions(administrator=True)
async def setdevlog(interaction: discord.Interaction):
    await interaction.response.defer()
    update_config(interaction.guild_id, dev_channel=str(interaction.channel_id))
    await interaction.followup.send("🛠️ Dev-Log channel locked.")

# ==========================================
# 🕵️‍♂️ SPY TOOLS
# ==========================================
@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    data = json.dumps({"content": message.content, "author": message.author.name, "time": datetime.now().strftime("%I:%M %p")})
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO snipes (channel_id, data) VALUES (?, ?)", (str(message.channel.id), data))
    conn.commit()

@bot.tree.command(name="snipe", description="Reveal the last deleted message here")
async def snipe(interaction: discord.Interaction):
    await interaction.response.defer()
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM snipes WHERE channel_id=?", (str(interaction.channel_id),))
    row = cursor.fetchone()
    if not row: return await interaction.followup.send("There's nothing to snipe here!")
    snipe_data = json.loads(row[0])
    await interaction.followup.send(f"🕵️‍♂️ **Sniped Message**\n**Author:** {snipe_data['author']} at {snipe_data['time']}\n**Message:** {snipe_data['content']}")

@bot.tree.command(name="tldr", description="Summarize the last 50 messages")
async def tldr(interaction: discord.Interaction):
    await interaction.response.defer()
    messages = [msg async for msg in interaction.channel.history(limit=50)]
    messages.reverse() 
    chat_log = "\n".join([f"{m.author.name}: {m.content}" for m in messages if not m.author.bot])
    if len(chat_log) < 50: return await interaction.followup.send("Not enough chat history.")
    prompt = f"Summarize this Discord chat log briefly using bullet points:\n\n{chat_log[-3000:]}"
    response = await groq_client.chat.completions.create(model=bot_settings["primary_model"], messages=[{"role": "user", "content": prompt}], temperature=0.5)
    await interaction.followup.send(f"📜 **Channel TL;DR:**\n{response.choices[0].message.content}")

# ==========================================
# 🛡️ ADMIN & UTILITY COMMANDS
# ==========================================
@bot.tree.command(name="purge", description="[ADMIN] Delete up to 100 recent messages")
@app_commands.default_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Successfully purged {len(deleted)} messages.", ephemeral=True)

@bot.tree.command(name="lockdown", description="[ADMIN] Freeze this channel")
@app_commands.default_permissions(manage_channels=True)
async def lockdown(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.followup.send("🔒 **CHANNEL LOCKDOWN INITIATED.**")

@bot.tree.command(name="unlock", description="[ADMIN] Lift the channel lockdown")
@app_commands.default_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.followup.send("🔓 **CHANNEL UNLOCKED.**")

@bot.tree.command(name="weather", description="Get real-time live weather (Defaults to Azhikode)")
async def weather(interaction: discord.Interaction, city: str = "Azhikode"):
    await interaction.response.defer()
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://wttr.in/{city}?format=3") as resp:
            if resp.status == 200: await interaction.followup.send(f"☁️ **Live Weather:**\n`{await resp.text()}`")
            else: await interaction.followup.send("❌ Connection failed.")

# ==========================================
# 🧠 MEMORY & CONFIG
# ==========================================
@bot.tree.command(name="personality", description="Set bot personality. Type 'default' for original AI.")
async def set_personality(interaction: discord.Interaction, bio: str):
    await interaction.response.defer()
    try:
        guild_id = interaction.guild_id or interaction.user.id
        if bio.strip().lower() == "default":
            update_config(guild_id, personality="")
            await interaction.followup.send("🧠 Personality reset. I have returned to my default state as Klein.")
        else:
            update_config(guild_id, personality=bio)
            await interaction.followup.send(f"Server personality locked: {bio}")
    except Exception as e: await interaction.followup.send(f"❌ **System Error:** `{e}`")

@bot.tree.command(name="setchannel", description="Bot talks here automatically")
async def set_channel(interaction: discord.Interaction):
    await interaction.response.defer()
    if not interaction.guild: return await interaction.followup.send("Servers only!")
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO active_channels (channel_id, guild_id) VALUES (?, ?)", (str(interaction.channel_id), str(interaction.guild_id)))
    conn.commit()
    await interaction.followup.send(f"👀 Now monitoring #{interaction.channel.name}.")

@bot.tree.command(name="unsetchannel", description="Stop auto-talking in this channel")
async def unset_channel(interaction: discord.Interaction):
    await interaction.response.defer()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM active_channels WHERE channel_id=?", (str(interaction.channel_id),))
    conn.commit()
    await interaction.followup.send("🛑 Stopped monitoring.")

@bot.tree.command(name="clearmemory", description="Forgets the conversation history in this specific channel")
async def clear_memory(interaction: discord.Interaction):
    await interaction.response.defer()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_memory WHERE channel_id=?", (str(interaction.channel_id),))
    conn.commit()
    await interaction.followup.send("🧠 Group chat memory wiped.")

@bot.tree.command(name="changemodel", description="Switch AI model")
@app_commands.choices(model_name=[
    app_commands.Choice(name="LLaMA 3.3 70B", value="llama-3.3-70b-versatile"),
    app_commands.Choice(name="LLaMA 3.1 8B", value="llama-3.1-8b-instant"),
    app_commands.Choice(name="Gemma 2 9B", value="gemma2-9b-it")
])
async def change_model(interaction: discord.Interaction, model_name: app_commands.Choice[str]):
    await interaction.response.defer()
    bot_settings["primary_model"] = model_name.value
    await interaction.followup.send(f"🔄 Switched to: **{model_name.name}**")

# ==========================================
# 🤖 AUTONOMOUS RESEARCH ENGINE (GATEKEEPER)
# ==========================================
async def needs_research(text):
    if len(text) < 15: return False
    prompt = f"Does this user message require a live web search for factual data or research? Answer ONLY 'YES' or 'NO'. Message: '{text}'"
    try:
        response = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0.0
        )
        return "YES" in response.choices[0].message.content.upper()
    except: return False

# ==========================================
# 💬 DATABASE-BACKED MESSAGE HANDLER (V3.0)
# ==========================================
user_cooldowns = {} # Anti-spam tracker

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    
    # --- ANTI-SPAM COOLDOWN ---
    now = time.time()
    user_id = message.author.id
    if user_id in user_cooldowns and now - user_cooldowns[user_id] < 1.5:
        return # Ignore messages sent faster than 1.5 seconds apart
    user_cooldowns[user_id] = now
    
    bot_stats["messages_processed"] += 1
    
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user.mentioned_in(message)
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM active_channels WHERE channel_id=?", (str(message.channel.id),))
    is_active_chan = bool(cursor.fetchone())

    if is_dm or is_mentioned or is_active_chan:
        guild_id = message.guild.id if message.guild else message.author.id
        toggles, custom_personality, _ = get_config(guild_id)
        user_text = message.clean_content.replace(f"@{bot.user.name}", "").strip()
        
        # --- AUTONOMOUS RESEARCH LOGIC ---
        if toggles.get("auto_research", True) and await needs_research(user_text):
            async with message.channel.typing():
                await message.reply("⏳ *Autonomous protocol triggered. Scraping the web for live data...*")
                def heavy_scrape():
                    try: return list(DDGS().text(user_text, max_results=4))
                    except: return []

                raw_data = await asyncio.to_thread(heavy_scrape)
                if raw_data:
                    web_context = "\n\n".join([f"DATA: {r['body']}" for r in raw_data])
                    system_msg = "You are Klein. Synthesize this live data into a brilliant, conversational answer."
                    try:
                        response = await groq_client.chat.completions.create(
                            model=bot_settings["primary_model"],
                            messages=[
                                {"role": "system", "content": system_msg},
                                {"role": "user", "content": f"Query: {user_text}\n\nDATA:\n{web_context}"}
                            ],
                            temperature=0.4
                        )
                        reply = response.choices[0].message.content
                        if len(reply) > 2000:
                            for i in range(0, len(reply), 1995): await message.reply(reply[i:i+1995])
                        else: await message.reply(reply)
                        return # Exit so we don't trigger the normal reply below
                    except Exception as e:
                        await send_dev_log(guild_id, f"Auto-Research failed: {e}")

        # --- NORMAL CONVERSATION FLOW ---
        ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
        dynamic_context = f" [System note: The current time is {ist_time.strftime('%I:%M %p')} IST.]"
        
        if custom_personality and custom_personality != "": 
            system_content = custom_personality + JAILBREAK_PROMPT + dynamic_context
        else: 
            system_content = "Your name is Klein. You are a helpful, intelligent AI assistant." + dynamic_context
            
        system_prompt = {"role": "system", "content": system_content}
        
        channel_key = str(message.channel.id)
        cursor.execute("SELECT history FROM chat_memory WHERE channel_id=?", (channel_key,))
        row = cursor.fetchone()
        current_memory = json.loads(row[0]) if row else []
            
        current_memory.append({"role": "user", "content": f"[{message.author.display_name}]: {user_text}"})
        if len(current_memory) > MAX_HISTORY: current_memory = current_memory[-MAX_HISTORY:]

        async with message.channel.typing():
            try:
                response = await groq_client.chat.completions.create(
                    model=bot_settings["primary_model"], messages=[system_prompt] + current_memory, temperature=0.8
                )
                reply = response.choices[0].message.content
            except Exception as e:
                await send_dev_log(guild_id, str(e))
                await asyncio.sleep(1)
                try:
                    response = await groq_client.chat.completions.create(
                        model=bot_settings["fallback_model"], messages=[system_prompt] + current_memory, temperature=0.8
                    )
                    reply = response.choices[0].message.content
                except Exception as fallback_e:
                    await send_dev_log(guild_id, str(fallback_e))
                    reply = f"Both models failed. *Use `/changemodel` to switch AI brains.*"

            current_memory.append({"role": "assistant", "content": reply})
            
            cursor.execute("REPLACE INTO chat_memory (channel_id, history) VALUES (?, ?)", (channel_key, json.dumps(current_memory)))
            conn.commit()
            
            if len(reply) > 2000:
                chunks = [reply[i:i+1995] for i in range(0, len(reply), 1995)]
                for chunk in chunks: await message.reply(chunk)
            else:
                await message.reply(reply)

keep_alive()
bot.run(DISCORD_TOKEN)