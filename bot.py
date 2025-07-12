import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
import json
import os
import asyncio

# === CONFIG ===
TOKEN = 'MTM5MzIwMjYxMTQzOTUzODI4MA.GhF7h6.Hduy6TKQXlGKGVrgvRfqGTyucSpuXywnTua_3cEN'
TRADE_CHANNEL_NAME = 'trade-signals'
FREE_CHANNEL_NAME = 'free-trade-signals'
SIGNALS_FILE = 'signals.json'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
scheduler = AsyncIOScheduler(timezone=timezone('Europe/Amsterdam'))


def load_signals():
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE, 'r') as f:
            return json.load(f)
    else:
        return {"daily_signals": [], "free_signals": []}


def save_signals(signals):
    with open(SIGNALS_FILE, 'w') as f:
        json.dump(signals, f, indent=2)


async def send_daily_signals():
    await bot.wait_until_ready()
    channel = discord.utils.get(bot.get_all_channels(), name=TRADE_CHANNEL_NAME)
    if not channel:
        print(f"Channel '{TRADE_CHANNEL_NAME}' not found.")
        return

    signals = load_signals()
    daily = signals["daily_signals"]

    if len(daily) < 2:
        await channel.send("⚠️ Not enough trade signals left.")
        return

    to_send = daily[:2]
    for signal in to_send:
        await channel.send(signal)

    signals["daily_signals"] = daily[2:]
    save_signals(signals)


async def send_free_signal():
    await bot.wait_until_ready()
    channel = discord.utils.get(bot.get_all_channels(), name=FREE_CHANNEL_NAME)
    if not channel:
        print(f"Channel '{FREE_CHANNEL_NAME}' not found.")
        return

    signals = load_signals()
    free = signals["free_signals"]

    if len(free) == 0:
        await channel.send("⚠️ No free signals left.")
        return

    message = free.pop(0)
    await channel.send(message)

    signals["free_signals"] = free
    save_signals(signals)
    
@bot.event
async def on_ready():
    with open("bot_online.txt", "w") as f:
        f.write("online")
    ...

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    scheduler.add_job(send_daily_signals, CronTrigger(hour=8, minute=0))
    scheduler.add_job(send_free_signal, CronTrigger(day_of_week='wed', hour=9, minute=0))
    scheduler.start()


@bot.command()
async def addsignals(ctx, signal_type: str):
    if signal_type not in ["daily", "free"]:
        await ctx.send("❌ Use `!addsignals daily` or `!addsignals free`.")
        return

    await ctx.send(f"✅ OK! Please reply to this message with the **{signal_type}** signal(s) you want to add.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', timeout=120.0, check=check)
        new_signals = [s.strip() for s in msg.content.strip().split("\n\n") if s.strip()]
        if not new_signals:
            await ctx.send("⚠️ No valid signals found.")
            return

        signals = load_signals()
        if signal_type == "daily":
            signals["daily_signals"].extend(new_signals)
        else:
            signals["free_signals"].extend(new_signals)

        save_signals(signals)
        await ctx.send(f"✅ Added {len(new_signals)} {signal_type} signal(s) to the list.")
    except asyncio.TimeoutError:
        await ctx.send("⌛ Timed out waiting for your signal input. Please try `!addsignals` again.")

bot.run(TOKEN)
