import discord
from discord.ext import commands
import os
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

RAID_THRESHOLD = 10
SPAM_THRESHOLD = 5
MENTION_THRESHOLD = 8

join_log = {}
message_log = {}

BLACKLISTED_DOMAINS = [
    "grabify", "iplogger", "blasze", "yoo.rs", "discord.gift",
    "discord-nitro", "free-nitro", "nitro-gift"
]

@bot.event
async def on_ready():
    print(f"Bot is online: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="Protecting Server"))

@bot.event
async def on_member_join(member):
    if member.bot: return
    now = datetime.utcnow()
    key = f"{member.guild.id}_{now.minute}"
    join_log.setdefault(key, []).append(member)

    recent = []
    for k in list(join_log.keys()):
        try:
            minute = int(k.split("_")[-1])
            time_key = now.replace(minute=minute, second=0, microsecond=0)
            if (now - time_key).total_seconds() < 60:
                recent.extend(join_log[k])
        except: pass

    if len(recent) > RAID_THRESHOLD:
        await member.guild.edit(verification_level=discord.VerificationLevel.highest)
        log = discord.utils.get(member.guild.text_channels, name="mod-log")
        if log:
            await log.send(f"RAID ALERT! {len(recent)} joins in 60s. Verification: HIGHEST")

@bot.event
async def on_message(message):
    if message.author.bot: return

    content = message.content.lower()
    if any(domain in content for domain in BLACKLISTED_DOMAINS):
        await message.delete()
        await message.channel.send(f"{message.author.mention} Scam links forbidden!", delete_after=5)
        return

    if len(message.mentions) > MENTION_THRESHOLD:
        await message.delete()
        await message.channel.send(f"{message.author.mention} Too many mentions!", delete_after=5)
        return

    user_id = message.author.id
    now = datetime.utcnow()
    message_log.setdefault(user_id, []).append(now)

    recent = [t for t in message_log[user_id] if (now - t).total_seconds() < 5]
    if len(recent) > SPAM_THRESHOLD:
        await message.delete()
        try:
            await message.author.timeout(timedelta(minutes=10), reason="Spam")
            await message.channel.send(f"{message.author.mention} Muted 10 min for spam.")
        except: pass

    message_log[user_id] = [t for t in message_log[user_id] if (now - t).total_seconds() < 10]
    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def lockdown(ctx):
    await ctx.guild.edit(verification_level=discord.VerificationLevel.highest)
    await ctx.send("Server LOCKED DOWN!")

@bot.command()
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    await ctx.guild.edit(verification_level=discord.VerificationLevel.medium)
    await ctx.send("Lockdown REMOVED.")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Bot online! Ping: {round(bot.latency*1000)}ms")

bot.run(os.getenv("BOT_TOKEN"))
