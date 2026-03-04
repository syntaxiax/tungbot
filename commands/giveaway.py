import discord
import asyncio
import random
import re
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import commands.giveaway_utils as giveaway_utils

EMBED_COLOR = 0xFF6B00
GIVEAWAY_ALLOWED_ROLES = {1476236683014836440}


def can_use_giveaway():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        if {r.id for r in interaction.user.roles} & GIVEAWAY_ALLOWED_ROLES:
            return True
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return False
    return app_commands.check(predicate)


def parse_duration(duration_str: str) -> int | None:
    match = re.match(r"^(\d+)(s|m|h|d)$", duration_str.strip().lower())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    return value * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]


async def run_giveaway(
    channel: discord.TextChannel,
    msg: discord.Message,
    view: "GiveawayView",
    prize: str,
    winner_count: int,
    seconds: int,
    ends_at: datetime,
):
    try:
        await asyncio.sleep(seconds)
    except asyncio.CancelledError:
        cancelled_embed = discord.Embed(
            title="🚫 Giveaway Cancelled",
            description=f"**Prize:** {prize}\n\nThis giveaway has been cancelled.",
            color=discord.Color.red(),
        )
        view.stop()
        for item in view.children:
            item.disabled = True
        await msg.edit(embed=cancelled_embed, view=view)
        giveaway_utils.active_giveaways.pop(msg.id, None)
        return

    entrants = view.entrants
    result_embed = discord.Embed(color=EMBED_COLOR)

    if not entrants:
        result_embed.title = "🎉 Giveaway Ended"
        result_embed.description = f"**Prize:** {prize}\n\nNo one entered the giveaway."
    else:
        chosen = random.sample(entrants, min(winner_count, len(entrants)))
        winners_mentions = ", ".join(w.mention for w in chosen)
        result_embed.title = "🎉 Giveaway Ended"
        result_embed.description = f"**Prize:** {prize}\n\n**Winner(s):** {winners_mentions}"
        await channel.send(content=f"🎊 Congrats {winners_mentions}! You won **{prize}**!")

    result_embed.timestamp = ends_at
    view.stop()
    for item in view.children:
        item.disabled = True

    await msg.edit(embed=result_embed, view=view)
    giveaway_utils.active_giveaways.pop(msg.id, None)


class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.entrants: list[discord.Member] = []

    @discord.ui.button(label="🎉 Enter", style=discord.ButtonStyle.green)
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.entrants:
            self.entrants.remove(interaction.user)
            await interaction.response.send_message("✅ You left the giveaway.", ephemeral=True)
        else:
            self.entrants.append(interaction.user)
            await interaction.response.send_message(
                f"🎉 You entered! Good luck! (Total entrants: {len(self.entrants)})", ephemeral=True
            )


class GiveawayModal(discord.ui.Modal, title="Create a Giveaway"):
    prize = discord.ui.TextInput(label="Prize", placeholder="e.g. Nitro, Steam game...", required=True, max_length=256)
    duration = discord.ui.TextInput(label="Duration", placeholder="e.g. 30s, 10m, 2h, 1d", required=True, max_length=10)
    winners = discord.ui.TextInput(label="Number of Winners", placeholder="e.g. 1", required=True, max_length=2, default="1")
    description = discord.ui.TextInput(label="Extra Info (optional)", placeholder="Any extra details...", required=False, style=discord.TextStyle.paragraph, max_length=1024)

    def __init__(self, ping: discord.Role | None, channel: discord.TextChannel):
        super().__init__()
        self.ping = ping
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        seconds = parse_duration(self.duration.value)
        if seconds is None:
            await interaction.response.send_message("❌ Invalid duration. Use `30s`, `10m`, `2h`, `1d`.", ephemeral=True)
            return

        try:
            winner_count = int(self.winners.value)
            if winner_count < 1:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Number of winners must be a positive number.", ephemeral=True)
            return

        ends_at = datetime.utcnow() + timedelta(seconds=seconds)
        ends_timestamp = int(ends_at.timestamp())

        embed = discord.Embed(title=f"🎉 {self.prize.value}", color=EMBED_COLOR)
        embed.add_field(name="Ends", value=f"<t:{ends_timestamp}:R> (<t:{ends_timestamp}:f>)", inline=False)
        embed.add_field(name="Winners", value=str(winner_count), inline=True)
        embed.add_field(name="Hosted by", value=interaction.user.mention, inline=True)
        if self.description.value:
            embed.add_field(name="Details", value=self.description.value, inline=False)
        embed.set_footer(text="Click 🎉 to enter!")

        view = GiveawayView()

        # Acknowledge the modal silently, then send the giveaway via channel directly
        await interaction.response.defer(ephemeral=True)

        msg = await self.channel.send(
            content=self.ping.mention if self.ping else None,
            embed=embed,
            view=view,
        )

        # Store the task before responding so cancel can find it immediately
        task = asyncio.create_task(
            run_giveaway(self.channel, msg, view, self.prize.value, winner_count, seconds, ends_at)
        )
        giveaway_utils.active_giveaways[msg.id] = task

        # Log to console so you can verify the ID
        print(f"[Giveaway] Started | message_id={msg.id} | prize={self.prize.value}")


class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="giveaway", description="Start a giveaway in this channel")
    @app_commands.describe(ping="Optional role to ping for the giveaway")
    @can_use_giveaway()
    async def giveaway(self, interaction: discord.Interaction, ping: discord.Role | None = None):
        modal = GiveawayModal(ping=ping, channel=interaction.channel)
        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaway(bot))
