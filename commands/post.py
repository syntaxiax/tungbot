import discord
import asyncio
import random
import re
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta

EMBED_COLOR = 0xFF6B00

GIVEAWAY_ALLOWED_ROLES = {1476236683014836440}

# Tracks active giveaways: message_id -> asyncio.Task
active_giveaways: dict[int, asyncio.Task] = {}


def can_use_giveaway():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        user_role_ids = {role.id for role in interaction.user.roles}
        if user_role_ids & GIVEAWAY_ALLOWED_ROLES:
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
    interaction: discord.Interaction,
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
        # Giveaway was cancelled
        cancelled_embed = discord.Embed(
            title="🚫 Giveaway Cancelled",
            description=f"**Prize:** {prize}\n\nThis giveaway has been cancelled.",
            color=discord.Color.red(),
        )
        view.stop()
        for item in view.children:
            item.disabled = True
        await msg.edit(embed=cancelled_embed, view=view)
        active_giveaways.pop(msg.id, None)
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
        await interaction.channel.send(
            content=f"🎊 Congrats {winners_mentions}! You won **{prize}**!"
        )

    result_embed.timestamp = ends_at

    view.stop()
    for item in view.children:
        item.disabled = True

    await msg.edit(embed=result_embed, view=view)
    active_giveaways.pop(msg.id, None)


class GiveawayModal(discord.ui.Modal, title="Create a Giveaway"):
    prize = discord.ui.TextInput(
        label="Prize",
        placeholder="e.g. Nitro, Steam game, custom role...",
        required=True,
        max_length=256,
    )
    duration = discord.ui.TextInput(
        label="Duration",
        placeholder="e.g. 30s, 10m, 2h, 1d",
        required=True,
        max_length=10,
    )
    winners = discord.ui.TextInput(
        label="Number of Winners",
        placeholder="e.g. 1",
        required=True,
        max_length=2,
        default="1",
    )
    description = discord.ui.TextInput(
        label="Extra Info (optional)",
        placeholder="Any extra details about the giveaway...",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=1024,
    )

    def __init__(self, ping: discord.Role | None):
        super().__init__()
        self.ping = ping

    async def on_submit(self, interaction: discord.Interaction):
        seconds = parse_duration(self.duration.value)
        if seconds is None:
            await interaction.response.send_message(
                "❌ Invalid duration. Use formats like `30s`, `10m`, `2h`, `1d`.", ephemeral=True
            )
            return

        try:
            winner_count = int(self.winners.value)
            if winner_count < 1:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Number of winners must be a positive number.", ephemeral=True
            )
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

        await interaction.response.defer(ephemeral=True)

        ping_content = self.ping.mention if self.ping else None
        msg = await interaction.channel.send(content=ping_content, embed=embed, view=view)

        await interaction.delete_original_response()

        # Start giveaway task and track it
        task = asyncio.create_task(
            run_giveaway(interaction, msg, view, self.prize.value, winner_count, seconds, ends_at)
        )
        active_giveaways[msg.id] = task


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


class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="giveaway", description="Start a giveaway in this channel")
    @app_commands.describe(ping="Optional role to ping for the giveaway")
    @can_use_giveaway()
    async def giveaway(
        self,
        interaction: discord.Interaction,
        ping: discord.Role | None = None,
    ):
        modal = GiveawayModal(ping=ping)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="giveaway-cancel", description="Cancel an active giveaway by its message ID")
    @app_commands.describe(message_id="The ID of the giveaway message")
    @can_use_giveaway()
    async def giveaway_cancel(
        self,
        interaction: discord.Interaction,
        message_id: str,
    ):
        try:
            mid = int(message_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid message ID.", ephemeral=True)
            return

        task = active_giveaways.get(mid)
        if not task:
            await interaction.response.send_message(
                "❌ No active giveaway found with that message ID.", ephemeral=True
            )
            return

        task.cancel()
        await interaction.response.send_message("✅ Giveaway cancelled.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaway(bot))
