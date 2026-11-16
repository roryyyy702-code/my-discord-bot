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
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="!ask [سؤالك] | Rory Bot 🤖"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # نظام اللفلات والنقاط
    author_id = message.author.id
    if author_id not in user_xp:
        user_xp[author_id] = {"xp": 0, "level": 1}
    user_xp[author_id]["xp"] += random.randint(5, 15)
    if user_xp[author_id]["xp"] >= user_xp[author_id]["level"] * 100:
        user_xp[author_id]["level"] += 1
        await message.channel.send(f"🎉 مبروك {message.author.mention}! صعدت إلى **المستوى {user_xp[author_id]['level']}**! 🚀")

    if "السلام عليكم" in message.content.lower():
        await message.channel.send(f"وعليكم السلام ورحمة الله وبركاته يا هلا بـ {message.author.mention} 🌸")

    await bot.process_commands(message)

# أمر الذكاء الاصطناعي
@bot.command(name='ask', aliases=['اسأل'])
async def ask(ctx, *, question: str):
    if not gemini_model:
        return await ctx.send("❌ مفتاح الذكاء الاصطناعي `GEMINI_API_KEY` غير مفعل في المنصة!")
    async with ctx.typing():
        try:
            response = gemini_model.generate_content(question)
            await ctx.send(f"🤖 **إجابة الذكاء الاصطناعي:**\n{response.text[:1900]}")
        except Exception as e:
            await ctx.send(f"⚠️ حدث خطأ: {e}")

# أمر قراءة الكلام (TTS)
@bot.command(name='say', aliases=['قول'])
async def say(ctx, *, text: str):
    if not ctx.author.voice:
        return await ctx.send("❌ لازم تكونين داخل روم صوتي!")
    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client or await channel.connect()
    if voice_client.channel != channel:
        await voice_client.move_to(channel)
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='ar')
        tts.save("tts.mp3")
        if voice_client.is_playing():
            voice_client.stop()
        voice_client.play(discord.FFmpegPCMAudio("tts.mp3"), after=lambda e: os.remove("tts.mp3") if os.path.exists("tts.mp3") else None)
        await ctx.message.add_reaction("🔊")
    except Exception as e:
        await ctx.send(f"⚠️ خطأ: {e}")

# أمر الأغاني
@bot.command(name='play', aliases=['شغل'])
async def play(ctx, *, search):
    if not ctx.author.voice:
        return await ctx.send("❌ ادخلي روم صوتي أول!")
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()
    async with ctx.typing():
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
        if 'entries' in data:
            data = data['entries'][0]
        source = await discord.FFmpegOpusAudio.from_probe(data['url'], **ffmpeg_options)
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        ctx.voice_client.play(source)
        await ctx.send(f"🎶 جاري تشغيل: **{data['title']}**")

@bot.command(name='stop', aliases=['ايقاف'])
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏹️ تم الإيقاف.")

@bot.command(name='rank', aliases=['لفلي'])
async def rank(ctx):
    data = user_xp.get(ctx.author.id, {"xp": 0, "level": 1})
    embed = discord.Embed(title=f"📊 رتبة {ctx.author.name}", color=discord.Color.blue())
    embed.add_field(name="المستوى:", value=str(data["level"]), inline=True)
    embed.add_field(name="النقاط:", value=str(data["xp"]), inline=True)
    await ctx.send(embed=embed)

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name='ترحيب') or member.guild.system_channel
    if channel:
        embed = discord.Embed(title="✨ نورت السيرفر!", description=f"أهلاً بك {member.mention} معنا 💖", color=discord.Color.purple())
        await channel.send(embed=embed)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! 🏓 Bot is online!')

if TOKEN:
    bot.run(TOKEN)
