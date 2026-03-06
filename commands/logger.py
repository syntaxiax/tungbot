import discord
from discord.ext import commands
from datetime import datetime

# ── Set the channel ID where logs will be sent ──
LOG_CHANNEL_ID = 1476236685430882406  # Replace with your log channel ID


class MessageLogger(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        # Ignore bots
        if message.author.bot:
            return

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return

        embed = discord.Embed(
            title="🗑️ Message Deleted",
            color=discord.Color.red(),
            timestamp=datetime.utcnow(),
        )
        embed.add_field(name="Author", value=f"{message.author} ({message.author.id})", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(
            name="Content",
            value=message.content or "*No text content (may have been an attachment)*",
            inline=False,
        )

        if message.attachments:
            embed.add_field(
                name="Attachments",
                value="\n".join(a.filename for a in message.attachments),
                inline=False,
            )

        embed.set_footer(text=f"Message ID: {message.id}")
        embed.set_thumbnail(url=message.author.display_avatar.url)

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        # Ignore bots and cases where content didn't change (e.g. embed loading)
        if before.author.bot:
            return
        if before.content == after.content:
            return

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return

        embed = discord.Embed(
            title="✏️ Message Edited",
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow(),
        )
        embed.add_field(name="Author", value=f"{before.author} ({before.author.id})", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.add_field(name="Before", value=before.content or "*empty*", inline=False)
        embed.add_field(name="After", value=after.content or "*empty*", inline=False)
        embed.add_field(name="Jump to Message", value=f"[Click here]({after.jump_url})", inline=False)
        embed.set_footer(text=f"Message ID: {before.id}")
        embed.set_thumbnail(url=before.author.display_avatar.url)

        await log_channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(MessageLogger(bot))
