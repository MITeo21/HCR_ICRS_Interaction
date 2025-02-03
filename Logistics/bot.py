# bot.py
import os
import random
from dotenv import load_dotenv

# 1
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

## Setup intents
intents_def = discord.Intents.default()  # This enables the default intents
intents_def.message_content = True

# 2
bot = commands.Bot(command_prefix='!', intents=intents_def)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='99', help='Responds with a random quote from Brooklyn 99')
async def nine_nine(ctx):
    brooklyn_99_quotes = [
        'I\'m the human form of the 💯 emoji.',
        'Bingpot!',
        (
            'Cool. Cool cool cool cool cool cool cool, '
            'no doubt no doubt no doubt no doubt.'
        ),
    ]

    response = random.choice(brooklyn_99_quotes)
    await ctx.send(response)

@bot.command(name='summon', help='Summons the ICRS bot to the <seat-number> requested')
async def summon(ctx, seat_num : int):
    response = f"Sending the bot to seat number {str(seat_num)} in the robotics lab"
    ## insert code that starts up the fetch command in navigation
    await ctx.send(response)

bot.run(TOKEN)