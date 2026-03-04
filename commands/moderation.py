import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta

MODERATION_ALLOWED_ROLES = {1476236683014836444, 1476236683014836445}


def has_mod_role(user: discord.Member) -> bool:
    if user.guild_permissions.administrator:
        return True
    return bool({r.id for r in user.roles} & MODERATION_ALLOWED_ROLES)


def can_moderate():
    async def predicate(interaction: discord.Interaction) -> bool:
        if has_mod_role(interaction.user):
            return True
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return False
    return app_commands.check(predicate)


USAGE = {
    "kick":   "**Usage:** `?kick @member [reason]`\nExample: `?kick @John spamming`",
    "ban":    "**Usage:** `?ban @member [reason]`\nExample: `?ban @John toxic behavior`",
    "unban":  "**Usage:** `?unban <user_id>`\nExample: `?unban 123456789012345678`",
    "mute":   "**Usage:** `?mute @member <minutes> [reason]`\nExample: `?mute @John 10 spamming`",
    "unmute": "**Usage:** `?unmute @member`\nExample: `?unmute @John`",
}


def usage_embed(command: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"❓ How to use ?{command}",
        description=USAGE[command],
        color=discord.Color.blurple(),
    )
    return embed


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────
    #  PREFIX COMMANDS
    # ────────────────────────────────────────────

    @commands.command(name="kick")
    async def prefix_kick(self, ctx: commands.Context, member: discord.Member = None, *, reason: str = "No reason provided"):
        if not has_mod_role(ctx.author):
            return
        if member is None:
            await ctx.send(embed=usage_embed("kick"))
            return
        if member == ctx.author:
            await ctx.send("❌ You can't kick yourself.")
            return
        if member.top_role >= ctx.author.top_role and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You can't kick someone with an equal or higher role.")
            return
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(title="👢 Member Kicked", color=discord.Color.orange())
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick that member.")

    @commands.command(name="ban")
    async def prefix_ban(self, ctx: commands.Context, member: discord.Member = None, *, reason: str = "No reason provided"):
        if not has_mod_role(ctx.author):
            return
        if member is None:
            await ctx.send(embed=usage_embed("ban"))
            return
        if member == ctx.author:
            await ctx.send("❌ You can't ban yourself.")
            return
        if member.top_role >= ctx.author.top_role and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You can't ban someone with an equal or higher role.")
            return
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(title="🔨 Member Banned", color=discord.Color.red())
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban that member.")

    @commands.command(name="unban")
    async def prefix_unban(self, ctx: commands.Context, user_id: str = None):
        if not has_mod_role(ctx.author):
            return
        if user_id is None:
            await ctx.send(embed=usage_embed("unban"))
            return
        try:
            uid = int(user_id)
            user = await self.bot.fetch_user(uid)
            await ctx.guild.unban(user)
            embed = discord.Embed(title="✅ Member Unbanned", color=discord.Color.green())
            embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send(embed=usage_embed("unban"))
        except discord.NotFound:
            await ctx.send("❌ That user is not banned or doesn't exist.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unban that user.")

    @commands.command(name="mute")
    async def prefix_mute(self, ctx: commands.Context, member: discord.Member = None, duration: int = None, *, reason: str = "No reason provided"):
        if not has_mod_role(ctx.author):
            return
        if member is None or duration is None:
            await ctx.send(embed=usage_embed("mute"))
            return
        if member == ctx.author:
            await ctx.send("❌ You can't mute yourself.")
            return
        if member.top_role >= ctx.author.top_role and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You can't mute someone with an equal or higher role.")
            return
        if duration < 1 or duration > 40320:
            await ctx.send("❌ Duration must be between 1 and 40320 minutes (28 days).")
            return
        try:
            await member.timeout(timedelta(minutes=duration), reason=reason)
            embed = discord.Embed(title="🔇 Member Muted", color=discord.Color.orange())
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Duration", value=f"{duration} minute(s)", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to mute that member.")

    @commands.command(name="unmute")
    async def prefix_unmute(self, ctx: commands.Context, member: discord.Member = None):
        if not has_mod_role(ctx.author):
            return
        if member is None:
            await ctx.send(embed=usage_embed("unmute"))
            return
        try:
            await member.timeout(None)
            embed = discord.Embed(title="🔊 Member Unmuted", color=discord.Color.green())
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unmute that member.")

    # ────────────────────────────────────────────
    #  SLASH COMMANDS
    # ────────────────────────────────────────────

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    @can_moderate()
    async def slash_kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member == interaction.user:
            await interaction.response.send_message("❌ You can't kick yourself.", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You can't kick someone with an equal or higher role.", ephemeral=True)
            return
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(title="👢 Member Kicked", color=discord.Color.orange())
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to kick that member.", ephemeral=True)

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="The member to ban", reason="Reason for the ban", delete_days="How many days of messages to delete (0-7)")
    @can_moderate()
    async def slash_ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", delete_days: int = 0):
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
            embed = discord.Embed(title="🔨 Member Banned", color=discord.Color.red())
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to ban that member.", ephemeral=True)

    @app_commands.command(name="unban", description="Unban a user by their ID")
    @app_commands.describe(user_id="The ID of the user to unban")
    @can_moderate()
    async def slash_unban(self, interaction: discord.Interaction, user_id: str):
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

    @app_commands.command(name="mute", description="Timeout a member so they can't talk")
    @app_commands.describe(member="The member to mute", duration="Duration in minutes", reason="Reason for the mute")
    @can_moderate()
    async def slash_mute(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
        if member == interaction.user:
            await interaction.response.send_message("❌ You can't mute yourself.", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You can't mute someone with an equal or higher role.", ephemeral=True)
            return
        if duration < 1 or duration > 40320:
            await interaction.response.send_message("❌ Duration must be between 1 and 40320 minutes.", ephemeral=True)
            return
        try:
            await member.timeout(timedelta(minutes=duration), reason=reason)
            embed = discord.Embed(title="🔇 Member Muted", color=discord.Color.orange())
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Duration", value=f"{duration} minute(s)", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to mute that member.", ephemeral=True)

    @app_commands.command(name="unmute", description="Remove a timeout from a member")
    @app_commands.describe(member="The member to unmute")
    @can_moderate()
    async def slash_unmute(self, interaction: discord.Interaction, member: discord.Member):
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
