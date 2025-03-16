import threading
import tkinter as tk
import asyncio
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Global variables to track the bot instance and its thread.
bot = None
bot_thread = None

def update_status(is_running):
    """Update the GUI status indicator."""
    if is_running:
        status_label.config(text="Bot Running", bg="green")
    else:
        status_label.config(text="Bot Stopped", bg="red")

def update_seat(seat_num):
    """Update the GUI to display the seat number."""
    seat_label.config(text=f"Seat Number: {seat_num}")

def update_requester(user):
    """Update the GUI to display the requester of the seat number."""
    requester_label.config(text=f"Requested by: {user}")

def create_bot():
    """Creates a new Discord bot instance with a summon command."""
    intents_def = discord.Intents.default()
    intents_def.message_content = True
    new_bot = commands.Bot(command_prefix='!', intents=intents_def)

    @new_bot.event
    async def on_ready():
        print(f'{new_bot.user.name} has connected to Discord!')
        # Update status indicator on the GUI
        root.after(0, update_status, True)

    @new_bot.command(name='summon', help='Summons the bot to a requested seat')
    async def summon(ctx, seat_num: int):
        user_id = ctx.author.id
        user_name = str(ctx.author)  # e.g., "username#1234"
        print(f"{user_name} (ID: {user_id}) requested the bot for seat number {seat_num}.")
        response = f"Sending the bot to seat number {seat_num}."
        # Update the GUI seat number and requester labels safely using root.after()
        root.after(0, update_seat, seat_num)
        root.after(0, update_requester, user_name)
        await ctx.send(response)

    return new_bot

def run_bot():
    global bot
    bot = create_bot()
    bot.run(TOKEN)
    # When bot.run() returns (after shutdown), update the status indicator.
    root.after(0, update_status, False)

def start_bot():
    global bot_thread
    if bot_thread is None or not bot_thread.is_alive():
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        print("Bot starting...")
        # Optionally, set the status to "stopped" until on_ready updates it.
        update_status(False)

def stop_bot():
    global bot
    if bot is not None and not bot.is_closed():
        try:
            future = asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
            future.result(timeout=10)  # Wait for shutdown to complete.
            print("Bot stopping...")
            update_status(False)
        except Exception as e:
            print("Error stopping bot:", e)
    else:
        print("Bot is already stopped.")
        update_status(False)

# -------------------------------
# Tkinter GUI Code
# -------------------------------
root = tk.Tk()
root.title("Discord Bot Controller")
root.geometry("300x220")

start_button = tk.Button(root, text="Start Bot", command=start_bot, width=20)
start_button.pack(pady=5)

stop_button = tk.Button(root, text="Stop Bot", command=stop_bot, width=20)
stop_button.pack(pady=5)

# Status indicator label: initially red (stopped)
status_label = tk.Label(root, text="Bot Stopped", bg="red", fg="white", font=("Helvetica", 16), width=15)
status_label.pack(pady=5)

# Seat number display label: shows the seat number from the summon command.
seat_label = tk.Label(root, text="Seat Number: None", font=("Helvetica", 14))
seat_label.pack(pady=5)

# Requester display label: shows the Discord user who made the request.
requester_label = tk.Label(root, text="Requested by: None", font=("Helvetica", 14))
requester_label.pack(pady=5)

root.mainloop()
