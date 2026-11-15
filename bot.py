import os
import discord
from discord.ext import commands

TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('Bot is ready!')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! 🏓')

if TOKEN:
    bot.run(TOKEN)
