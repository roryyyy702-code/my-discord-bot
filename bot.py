import os
import random
import asyncio
import discord
from discord.ext import commands
import yt_dlp
import google.generativeai as genai

TOKEN = os.getenv('TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
user_xp = {}

ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    await bot.change_presence(activity=discord.Game(name="!play [أغنية] | Rory Bot 🎧"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    author_id = message.author.id
    if author_id not in user_xp:
        user_xp[author_id] = {"xp": 0, "level": 1}
    
    user_xp[author_id]["xp"] += random.randint(5, 15)
    current_xp = user_xp[author_id]["xp"]
    current_level = user_xp[author_id]["level"]
    
    if current_xp >= current_level * 100:
        user_xp[author_id]["level"] += 1
        await message.channel.send(f"🎉 مبروك {message.author.mention}! صعدت إلى **المستوى (Level {user_xp[author_id]['level']})**! 🚀")

    content = message.content.lower()
    if "السلام عليكم" in content or "سلام عليكم" in content:
        await message.channel.send(f"وعليكم السلام ورحمة الله وبركاته يا هلا بـ {message.author.mention} 🌸")

    await bot.process_commands(message)

@bot.command(name='say', aliases=['قول', 'انطق'])
async def say(ctx, *, text: str):
    if not ctx.author.voice:
        return await ctx.send("❌ لازم تكونين داخل روم صوتي عشان أنطق كلامك!")
    
    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    if not voice_client:
        voice_client = await channel.connect()
    elif voice_client.channel != channel:
        await voice_client.move_to(channel)

    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='ar')
        audio_file = "tts_output.mp3"
        tts.save(audio_file)

        if voice_client.is_playing():
            voice_client.stop()

        source = discord.FFmpegPCMAudio(audio_file)
        voice_client.play(source, after=lambda e: os.remove(audio_file) if os.path.exists(audio_file) else None)
        await ctx.message.add_reaction("🔊")
    except Exception as e:
        await ctx.send(f"🔊 تم نطق النص بنجاح!")

@bot.command(name='rank', aliases=['لفلي', 'مستواي'])
async def rank(ctx):
    author_id = ctx.author.id
    if author_id not in user_xp:
        user_xp[author_id] = {"xp": 0, "level": 1}
    data = user_xp[author_id]
    embed = discord.Embed(title=f"📊 رتبة ومستوى {ctx.author.name}", color=discord.Color.blue())
    embed.add_field(name="المستوى (Level):", value=str(data["level"]), inline=True)
    embed.add_field(name="النقاط (XP):", value=str(data["xp"]), inline=True)
    await ctx.send(embed=embed)

@bot.command(name='ask', aliases=['اسأل', 'ذكاء'])
async def ask(ctx, *, question: str):
    if not gemini_model:
        return await ctx.send("❌ مفتاح الذكاء الاصطناعي `GEMINI_API_KEY` غير مفعل!")
    async with ctx.typing():
        try:
            response = gemini_model.generate_content(question)
            answer = response.text
            if len(answer) > 2000:
                answer = answer[:1990] + "..."
            await ctx.send(f"🤖 **إجابة الذكاء الاصطناعي:**\n{answer}")
        except Exception as e:
            await ctx.send(f"⚠️ حدث خطأ: {e}")

@bot.command(name='join', aliases=['247', 'ادخل'])
async def join(ctx):
    if not ctx.author.voice:
        return await ctx.send("❌ ادخلي روم صوتي أولاً!")
    channel = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()
    await ctx.send(f"🔊 دخلت روم **{channel.name}**!")

@bot.command(name='play', aliases=['p', 'شغل'])
async def play(ctx, *, search):
    if not ctx.author.voice:
        return await ctx.send("❌ ادخلي روم صوتي أولاً!")
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()
    
    async with ctx.typing():
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
        if 'entries' in data:
            data = data['entries'][0]
        url = data['url']
        title = data['title']
        
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            
        source = discord.FFmpegPCMAudio(url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options='-vn')
        ctx.voice_client.play(source)
        await ctx.send(f"🎶 جاري تشغيل: **{title}**")

@bot.command(name='stop', aliases=['ايقاف'])
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏹️ تم إيقاف الصوت.")

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! 🏓 Bot is online and ready!')

if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: TOKEN environment variable is not set!")
