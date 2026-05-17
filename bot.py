import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import requests
import feedparser

# Load .env
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# =====================================
# CONFIG

last_price = None

@tasks.loop(minutes=5)
async def price_monitor():
    global last_price

    try:
        url = (
            "https://api.dexscreener.com/"
            "latest/dex/pairs/"
            "algorand/YGVU3WZ3B3U5A5AEHH7TW4VRBBNF7GI53XHFUBCLZCSO6N34PF32KFMMWQ"
        )

        response = requests.get(url)
        data = response.json()

        pair = data.get("pair")

        if not pair:
            return

        current_price = float(
            pair["priceUsd"]
        )

        if last_price is None:
            last_price = current_price
            return

        percent_change = (
            (current_price - last_price)
            / last_price
        ) * 100

        if abs(percent_change) >= 10:

            channel = bot.get_channel(
                X_CHANNEL_ID
            )

            direction = (
                "📈 UP"
                if percent_change > 0
                else "📉 DOWN"
            )

            await channel.send(
                f"🚨 STEAK ALERT\n\n"
                f"STEAK is {direction} "
                f"{abs(percent_change):.2f}%"
            )

            last_price = current_price

    except Exception as e:
        print(
            "Price alert error:",
            e
        )
# =====================================

# Steak ASA ID
STEAK_ASA_ID = 2595619475

# Burn wallet
BURN_ADDRESS = "BNFIREKGRXEHCFOEQLTX3PU5SUCMRKDU7WHNBGZA4SXPW42OAHZBP7BPHY"

# Discord channel IDs
BURN_CHANNEL_ID = 1316903981255098438
X_CHANNEL_ID = 1320482531908522075

# SteakPool X username
X_USERNAME = "steakpool"

# Track latest burn tx
last_tx_id = None

# Track latest X post
last_post_link = None


# =====================================
# DISCORD SETUP
# =====================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =====================================
# BOT READY
# =====================================

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

    # Prevent duplicate task start
    if not burn_monitor.is_running():
        burn_monitor.start()

    if not x_monitor.is_running():
        x_monitor.start()
    if not price_monitor.is_running():
        price_monitor.start()


# =====================================
# COMMANDS
# =====================================

@bot.command()
async def ping(ctx):
    await ctx.send("🥩 Steak Sentinel is alive!")


@bot.command(name="steak-price")
async def steak_price(ctx):
    try:
        url = (
            "https://api.dexscreener.com/"
            "latest/dex/pairs/algorand/YGVU3WZ3B3U5A5AEHH7TW4VRBBNF7GI53XHFUBCLZCSO6N34PF32KFMMWQ"
        )

        response = requests.get(url)
        data = response.json()

        pair = data.get("pair")

        if not pair:
            await ctx.send(
                "❌ Could not fetch SteakPool data."
            )
            return

        price = pair.get("priceUsd", "N/A")
        change = pair.get(
            "priceChange", {}
        ).get("h24", "N/A")

        volume = pair.get(
            "volume", {}
        ).get("h24", "N/A")

        liquidity = pair.get(
            "liquidity", {}
        ).get("usd", "N/A")

        embed = discord.Embed(
            title="🥩 STEAKPOOL LIVE UPDATE",
            description="Official SteakPool token stats",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="💰 Price",
            value=f"${price}",
            inline=False
        )

        embed.add_field(
            name="📈 24H Change",
            value=f"{change}%",
            inline=True
        )

        embed.add_field(
            name="📊 24H Volume",
            value=f"${volume}",
            inline=True
        )

        embed.add_field(
            name="💧 Liquidity",
            value=f"${liquidity}",
            inline=False
        )

        embed.set_footer(
            text="Steak Sentinel"
        )

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(
            f"❌ Error: {str(e)}"
        )

@bot.command(name="burned")
async def burned(ctx):

    if not burn_history:
        await ctx.send(
            "🔥 No burns recorded yet."
        )
        return

    total_burned = sum(
        burn["amount"]
        for burn in burn_history
    )

    latest_burn = burn_history[-1]

    embed = discord.Embed(
        title="🔥 STEAK Burn Stats",
        color=discord.Color.red()
    )

    embed.add_field(
        name="Last Burn",
        value=f"{latest_burn['amount']:,.2f} STEAK",
        inline=False
    )

    embed.add_field(
        name="Total Recorded Burns",
        value=f"{total_burned:,.2f} STEAK",
        inline=False
    )

    embed.add_field(
        name="Burn Events",
        value=f"{len(burn_history)}",
        inline=False
    )

    await ctx.send(embed=embed)
# =====================================
# BURN MONITOR
# =====================================

@tasks.loop(seconds=60)
async def burn_monitor():
    global last_tx_id

    try:
        url = (
            f"https://mainnet-idx.algonode.cloud/"
            f"v2/accounts/{BURN_ADDRESS}/transactions"
        )

        response = requests.get(url)
        data = response.json()

        txns = data.get(
            "transactions", []
        )

        if not txns:
            return

        latest_tx = txns[0]
        tx_id = latest_tx.get("id")

        # Avoid duplicate alerts
        if tx_id == last_tx_id:
            return

        asset_transfer = latest_tx.get(
            "asset-transfer-transaction"
        )

        if not asset_transfer:
            return

        asset_id = asset_transfer.get(
            "asset-id"
        )

        # Only Steak token
        if asset_id != STEAK_ASA_ID:
            return

        amount = asset_transfer.get(
            "amount", 0
        )
        amount = amount / 1_000_000
        burn_history.append({
            "tx_id": tx_id,
            "amount": amount
        })
        channel = bot.get_channel(BURN_CHANNEL_ID
        )

        if channel:
            embed = discord.Embed(
                title="🔥 STEAK BURN ALERT",
                color=discord.Color.red()
            )

            embed.add_field(
                name="Amount Burned",
                value=f"{amount:,.2f} STEAK",
                inline=False
            )

            explorer_link = (
                f"https://allo.info/tx/{tx_id}"
            )

            embed.add_field(
                name="🔗 View Transaction",
                value=f"[Open in Explorer]({explorer_link})",
                inline=False
            )

            embed.set_footer(
                text="Steak Sentinel Burn Tracker"
            )

            await channel.send(
                embed=embed
            )

        last_tx_id = tx_id

    except Exception as e:
        print(
            "Burn monitor error:",
            e
        )


# =====================================
# X UPDATE MONITOR
# =====================================

@tasks.loop(seconds=120)
async def x_monitor():
    global last_post_link

    try:
        rss_url = (
            f"https://nitter.net/"
            f"{X_USERNAME}/rss"
        )

        feed = feedparser.parse(
            rss_url
        )

        if not feed.entries:
            return

        latest_post = feed.entries[0]

        post_title = latest_post.title
        post_link = latest_post.link

        # Avoid duplicate alerts
        if post_link == last_post_link:
            return

        channel = bot.get_channel(
            X_CHANNEL_ID
        )

        if channel:
            embed = discord.Embed(
                title="📢 New SteakPool X Update",
                description=post_title,
                color=discord.Color.blue()
            )

            embed.add_field(
                name="🔗 View Post",
                value=post_link,
                inline=False
            )

            embed.set_footer(
                text="Steak Sentinel X Tracker"
            )

            await channel.send(
                "@everyone 🚨 New SteakPool update!",
                embed=embed
            )

        last_post_link = post_link

    except Exception as e:
        print(
            "X monitor error:",
            e
        )


# =====================================
# RUN BOT
# =====================================

bot.run(TOKEN)