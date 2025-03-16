# bot.py

import os
from dotenv import load_dotenv

# Discord API imports
import discord
from discord.ext import commands

# ROS imports
import rospy
from std_msgs.msg import Int64

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

## ROS Publisher Node

rospy.init_node('icrs_discord_bot', anonymous=True)
pub = rospy.Publisher('icrs_discord_bot', Int64, queue_size=10)

## Setup intents
intents_def = discord.Intents.default()  # This enables the default intents
intents_def.message_content = True

# 2
bot = commands.Bot(command_prefix='!', intents=intents_def)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='summon', help='Summons the ICRS bot to the <seat-number> requested')
async def summon(ctx, seat_num: int):
    # Capture the user ID using the command context.
    user_id = ctx.author.id  # This collects the member's unique ID [3]
    print(f"{user_id} has requested the bot to be summoned to seat number {seat_num}.")

    pub.publish(seat_num)
    
    # Fetch the box information for the user. Convert user_id to str if needed.
    # box_info = fetch_box_by_user(str(user_id))
    
    # Build the response message including seat number and box info.
    response = (
        f"Sending the bot to seat number {seat_num} in the robotics lab."
    )
    await ctx.send(response)

## TODO: Need code to initialise SLAM and navigation

bot.run(TOKEN)
