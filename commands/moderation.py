import discord
from discord import app_commands
from discord.ext import commands

MODERATION_ALLOWED_ROLES = {1476236683014836444, 1476236683014836445}


def can_moderate():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        if {r.id for r in interaction.user.roles} & MODERATION_ALLOWED_ROLES:
            return True
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return False
    return app_commands.check(predicate)


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── KICK ──
    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(
        member="The member to kick",
        reason="Reason for the kick",
    )
    @can_moderate()
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided",
    ):
        if member == interaction.user:
            await interaction.response.send_message("❌ You can't kick yourself.", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You can't kick someone with an equal or higher role.", ephemeral=True)
            return

        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="👢 Member Kicked",
                color=discord.Color.orange(),
            )
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to kick that member.", ephemeral=True)

    # ── BAN ──
    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(
        member="The member to ban",
        reason="Reason for the ban",
        delete_days="How many days of messages to delete (0-7)",
    )
    @can_moderate()
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided",
        delete_days: int = 0,
    ):
        if member == interaction.user:
            await interaction.response.send_message("❌ You can't ban yourself.", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You can't ban someone with an equal or higher role.", ephemeral=True)
            return
        if not 0 <= delete_days <= 7:
            await interaction.response.send_message("❌ Delete days must be between 0 and 7.", ephemeral=True)
            return

        try:
            await member.ban(reason=reason, delete_message_days=delete_days)
            embed = discord.Embed(
                title="🔨 Member Banned",
                color=discord.Color.red(),
            )
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            if delete_days > 0:
                embed.add_field(name="Messages Deleted", value=f"Last {delete_days} day(s)", inline=False)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to ban that member.", ephemeral=True)

    # ── UNBAN ──
    @app_commands.command(name="unban", description="Unban a user by their ID")
    @app_commands.describe(user_id="The ID of the user to unban")
    @can_moderate()
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
    ):
        try:
            uid = int(user_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID.", ephemeral=True)
            return

        try:
            user = await self.bot.fetch_user(uid)
            await interaction.guild.unban(user)
            embed = discord.Embed(title="✅ Member Unbanned", color=discord.Color.green())
            embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            await interaction.response.send_message(embed=embed)
        except discord.NotFound:
            await interaction.response.send_message("❌ That user is not banned or doesn't exist.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to unban that user.", ephemeral=True)

    # ── MUTE (timeout) ──
    @app_commands.command(name="mute", description="Timeout a member so they can't talk")
    @app_commands.describe(
        member="The member to mute",
        duration="Duration in minutes",
        reason="Reason for the mute",
    )
    @can_moderate()
    async def mute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration: int,
        reason: str = "No reason provided",
    ):
        if member == interaction.user:
            await interaction.response.send_message("❌ You can't mute yourself.", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You can't mute someone with an equal or higher role.", ephemeral=True)
            return
        if duration < 1 or duration > 40320:  # Discord max is 28 days (40320 minutes)
            await interaction.response.send_message("❌ Duration must be between 1 and 40320 minutes (28 days).", ephemeral=True)
            return

        try:
            from datetime import timedelta
            await member.timeout(timedelta(minutes=duration), reason=reason)
            embed = discord.Embed(title="🔇 Member Muted", color=discord.Color.orange())
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Duration", value=f"{duration} minute(s)", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to mute that member.", ephemeral=True)

    # ── UNMUTE ──
    @app_commands.command(name="unmute", description="Remove a timeout from a member")
    @app_commands.describe(member="The member to unmute")
    @can_moderate()
    async def unmute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ):
        try:
            await member.timeout(None)
            embed = discord.Embed(title="🔊 Member Unmuted", color=discord.Color.green())
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to unmute that member.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
