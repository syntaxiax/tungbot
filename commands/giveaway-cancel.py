import discord
from discord import app_commands
from discord.ext import commands
import commands.giveaway_utils as giveaway_utils

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


class GiveawayCancel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="giveaway-cancel", description="Cancel an active giveaway by its message ID")
    @app_commands.describe(message_id="The ID of the giveaway message")
    @can_use_giveaway()
    async def giveaway_cancel(self, interaction: discord.Interaction, message_id: str):
        try:
            mid = int(message_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid message ID.", ephemeral=True)
            return

        print(f"[Giveaway Cancel] Looking for message_id={mid} | active={list(giveaway_utils.active_giveaways.keys())}")

        task = giveaway_utils.active_giveaways.get(mid)
        if not task or task.done():
            await interaction.response.send_message("❌ No active giveaway found with that message ID.", ephemeral=True)
            return

        task.cancel()
        await interaction.response.send_message("✅ Giveaway cancelled.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawayCancel(bot))
