import discord
import asyncio
import random
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import re

EMBED_COLOR = 0xFF6B00


def parse_duration(duration_str: str) -> int | None:
    """Convert strings like 10s, 5m, 2h, 1d to seconds."""
    pattern = r"^(\d+)(s|m|h|d)$"
    match = re.match(pattern, duration_str.strip().lower())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    return value * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]


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
        # Validate duration
        seconds = parse_duration(self.duration.value)
        if seconds is None:
            await interaction.response.send_message(
                "❌ Invalid duration. Use formats like `30s`, `10m`, `2h`, `1d`.",
                ephemeral=True,
            )
            return

        # Validate winner count
        try:
            winner_count = int(self.winners.value)
            if winner_count < 1:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Number of winners must be a positive number.",
                ephemeral=True,
            )
            return

        ends_at = datetime.utcnow() + timedelta(seconds=seconds)
        ends_timestamp = int(ends_at.timestamp())

        embed = discord.Embed(
            title=f"🎉 {self.prize.value}",
            color=EMBED_COLOR,
        )
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

        # Wait then pick winners
        await asyncio.sleep(seconds)

        # Reload view to get final entrants
        entrants = view.entrants

        result_embed = discord.Embed(color=EMBED_COLOR)

        if not entrants:
            result_embed.title = "🎉 Giveaway Ended"
            result_embed.description = f"**Prize:** {self.prize.value}\n\nNo one entered the giveaway."
        else:
            chosen = random.sample(entrants, min(winner_count, len(entrants)))
            winners_mentions = ", ".join(w.mention for w in chosen)
            result_embed.title = "🎉 Giveaway Ended"
            result_embed.description = f"**Prize:** {self.prize.value}\n\n**Winner(s):** {winners_mentions}"
            await interaction.channel.send(
                content=f"🎊 Congrats {winners_mentions}! You won **{self.prize.value}**!"
            )

        result_embed.set_footer(text=f"Ended at")
        result_embed.timestamp = ends_at

        # Disable the button and update embed
        view.stop()
        for item in view.children:
            item.disabled = True

        await msg.edit(embed=result_embed, view=view)


class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.entrants: list[discord.Member] = []

    @discord.ui.button(label="🎉 Enter", style=discord.ButtonStyle.green)
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.entrants:
            self.entrants.remove(interaction.user)
            await interaction.response.send_message(
                "✅ You left the giveaway.", ephemeral=True
            )
        else:
            self.entrants.append(interaction.user)
            await interaction.response.send_message(
                f"🎉 You entered the giveaway! Good luck! (Total entrants: {len(self.entrants)})",
                ephemeral=True,
            )


class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="giveaway", description="Start a giveaway in this channel")
    @app_commands.describe(ping="Optional role to ping for the giveaway")
    async def giveaway(
        self,
        interaction: discord.Interaction,
        ping: discord.Role | None = None,
    ):
        modal = GiveawayModal(ping=ping)
        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaway(bot))
