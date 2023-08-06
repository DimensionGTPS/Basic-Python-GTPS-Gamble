import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
import sqlite3
import random

connection = sqlite3.connect("economy.db")
cursor = connection.cursor()

def get_currency_name(currency):
    if currency.lower() == "wl":
        return "world_locks"
    elif currency.lower() == "dl":
        return "diamond_locks"
    elif currency.lower() == "bgl":
        return "blue_gem_locks"
    else:
        return None

cursor.execute("CREATE TABLE IF NOT EXISTS economy (user_id INTEGER PRIMARY KEY, world_locks INTEGER, diamond_locks INTEGER, blue_gem_locks INTEGER)")
connection.commit()

def get_balance(user_id):
    cursor.execute("SELECT world_locks, diamond_locks, blue_gem_locks FROM economy WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        return result
    else:
        cursor.execute("INSERT INTO economy (user_id, world_locks, diamond_locks, blue_gem_locks) VALUES (?, ?, ?, ?)", (user_id, 10, 0, 0))
        connection.commit()
        return (10, 0, 0)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
slash = SlashCommand(bot, sync_commands=True)

@bot.event
async def on_ready():
    print("Credits : Dimension")
    await slash.register_global_commands()

wlemoji = "<:wl:1137454234170818704>"
dlemoji = "<:dl:1137454230546948268>"
bglemoji = "<:bgl:1137454228814712913>"#put here \:dl: so u get id for emoji's

@slash.slash(name="balance", description="Shows your balance.")
async def balance(ctx: SlashContext):
    user_id = ctx.author_id
    balance = get_balance(user_id)
    world_locks, diamond_locks, blue_gem_locks = balance

    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s Balance",
        description=(
            f"{wlemoji} World Locks: {world_locks}\n"
            f"{dlemoji} Diamond Locks: {diamond_locks}\n"
            f"{bglemoji} Blue Gem Locks: {blue_gem_locks}"
        ),
        color=discord.Color.green(),
    )
    await ctx.send(embed=embed)

def is_owner():
    async def predicate(ctx):
        return ctx.author.id == 1003670911750246462
    return commands.check(predicate)

def gamble_currency(user_id, currency_name, amount):
    cursor.execute(f"SELECT {currency_name} FROM economy WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        current_balance = result[0]
    else:
        default_balance = 10 if currency_name == "world_locks" else 0
        cursor.execute("INSERT INTO economy (user_id, world_locks, diamond_locks, blue_gem_locks) VALUES (?, ?, ?, ?)", (user_id, default_balance, default_balance, default_balance))
        connection.commit()
        current_balance = default_balance

    if amount > current_balance:
        return None

    if random.random() < 0.5:
        new_balance = current_balance + amount
        gamble_result = "Win"
    else:
        new_balance = current_balance - amount
        gamble_result = "Loss"

    cursor.execute(f"UPDATE economy SET {currency_name} = ? WHERE user_id = ?", (new_balance, user_id))
    connection.commit()

    return new_balance, gamble_result

@slash.slash(name="gamble", description="Gamble a certain amount of currency.")
async def gamble(ctx: SlashContext, currency: str, amount: int):
    user_id = ctx.author_id
    currency_name = get_currency_name(currency)
    if not currency_name:
        await ctx.send("Invalid currency shortcut. Use `wl`, `dl`, or `bgl`.")
        return

    if amount <= 0:
        await ctx.send("Amount must be a positive number.")
        return

    new_balance, gamble_result = gamble_currency(user_id, currency_name, amount)

    if new_balance is None:
        await ctx.send("Not enough currency to gamble.")
        return

    if currency == "wl":
        gg=wlemoji
    else:
        if currency=='bgl':
            gg=bglemoji
        elif currency =='dl':
            gg=dlemoji

    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s Gambling Result",
        description=f"Amount Gambled: {amount} {currency.upper()}\nResult: {gamble_result}\nNew Balance: {new_balance} {gg}",
        color=discord.Color.green() if gamble_result == "Win" else discord.Color.red(),
    )
    await ctx.send(embed=embed)

@slash.slash(name="mine", description="Mine and get a random amount of World Locks (1 to 5).")
async def mine(ctx: SlashContext):
    user_id = ctx.author_id
    mined_amount = random.randint(1, 5)
    cursor.execute("UPDATE economy SET world_locks = world_locks + ? WHERE user_id = ?", (mined_amount, user_id))
    connection.commit()
    cursor.execute("SELECT world_locks FROM economy WHERE user_id = ?", (user_id,))
    new_balance = cursor.fetchone()[0]
    embed = discord.Embed(
        title=f"{ctx.author.display_name} mined {mined_amount} World Locks!",
        description=f"New Balance: {new_balance} {wlemoji}",
        color=discord.Color.green(),
    )
    await ctx.send(embed=embed)

@slash.slash(name="reset", description="Reset user or all balances.", permissions=is_owner())
async def reset(ctx: SlashContext, user: discord.User = None):
    if user is None:
        cursor.execute("UPDATE economy SET world_locks = 10, diamond_locks = 0, blue_gem_locks = 0")
        connection.commit()
        await ctx.send("All user balances have been reset.")
    else:
        user_id = user.id
        cursor.execute("UPDATE economy SET world_locks = 10, diamond_locks = 0, blue_gem_locks = 0 WHERE user_id = ?", (user_id,))
        connection.commit()
        await ctx.send(f"{user.display_name}'s balance has been reset.")

def give_currency(user_id, currency_name, amount):
    cursor.execute(f"SELECT {currency_name} FROM economy WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        current_balance = result[0]
    else:
        default_balance = 10 if currency_name == "world_locks" else 0
        cursor.execute("INSERT INTO economy (user_id, world_locks, diamond_locks, blue_gem_locks) VALUES (?, ?, ?, ?)", (user_id, default_balance, default_balance, default_balance))
        connection.commit()
        current_balance = default_balance

    new_balance = current_balance + amount
    cursor.execute(f"UPDATE economy SET {currency_name} = ? WHERE user_id = ?", (new_balance, user_id))
    connection.commit()

    return new_balance

@slash.slash(name="give", description="Give currency to a mentioned user.")
@is_owner()
async def give(ctx: SlashContext, user: discord.User, currency: str, amount: int):
    user_id = user.id
    currency_name = get_currency_name(currency)
    if not currency_name:
        await ctx.send("Invalid currency shortcut. Use `wl`, `dl`, or `bgl`.")
        return

    if amount <= 0:
        await ctx.send("Amount must be a positive number.")
        return

    new_balance = give_currency(user_id, currency_name, amount)

    embed = discord.Embed(
        title=f"Gave {user.display_name} {amount} {currency.upper()}",
        description=f"New Balance: {new_balance} {currency.upper()}",
        color=discord.Color.green(),
    )
    await ctx.send(embed=embed)

token = "tokenhere papa"
bot.run(token)
