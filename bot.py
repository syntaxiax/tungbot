import os
import discord
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)

SKIP = {"giveaway_utils"}


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def run_health_server():
    server = HTTPServer(("0.0.0.0", 8000), HealthHandler)
    server.serve_forever()


threading.Thread(target=run_health_server, daemon=True).start()


@bot.event
async def on_ready():
    for filename in os.listdir("./commands"):
        if filename.endswith(".py"):
            name = filename[:-3]
            if name in SKIP:
                continue
            cog_name = f"commands.{name}"
            try:
                await bot.load_extension(cog_name)
                print(f"✅ Loaded: {cog_name}")
            except Exception as e:
                print(f"❌ Failed to load {cog_name}: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

    print(f"\n🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"📡 Connected to {len(bot.guilds)} server(s)")

    await bot.change_presence(
        activity=discord.Game(name="Brainrot Wave Defense")
    )


bot.run(TOKEN)
