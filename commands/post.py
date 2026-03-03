import discord
from discord import app_commands
from discord.ext import commands

EMBED_COLOR = 0xFF6B00

POST_ALLOWED_ROLES = {1476236683014836445, 1476236683014836444}


def can_use_post():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        user_role_ids = {role.id for role in interaction.user.roles}
        if user_role_ids & POST_ALLOWED_ROLES:
            return True
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return False
    return app_commands.check(predicate)


class PostModal(discord.ui.Modal, title="Create a Post"):
    post_title = discord.ui.TextInput(
        label="Title",
        placeholder="Enter a title...",
        required=True,
        max_length=256,
    )
    description = discord.ui.TextInput(
        label="Main Text",
        placeholder="Enter the main content... (optional)",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=4000,
    )

    def __init__(self, ping: discord.Role | None, file: discord.Attachment | None):
        super().__init__()
        self.ping = ping
        self.file = file

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=self.post_title.value,
            description=self.description.value or None,
            color=EMBED_COLOR,
        )
        embed.set_footer(
            text=f"Posted by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )

        discord_file = None
        if self.file:
            discord_file = await self.file.to_file()
            if any(self.file.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]):
                embed.set_image(url=f"attachment://{self.file.filename}")

        ping_content = self.ping.mention if self.ping else None

        await interaction.response.defer(ephemeral=True)

        kwargs = {"content": ping_content, "embed": embed}
        if discord_file is not None:
            kwargs["file"] = discord_file

        await interaction.channel.send(**kwargs)
        await interaction.delete_original_response()


class Post(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="post", description="Create a formatted embed post in this channel")
    @app_commands.describe(
        file="Optional image or file to attach to the post",
        ping="Optional role to ping with the post",
    )
    @can_use_post()
    async def post(
        self,
        interaction: discord.Interaction,
        file: discord.Attachment | None = None,
        ping: discord.Role | None = None,
    ):
        modal = PostModal(ping=ping, file=file)
        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot):
    await bot.add_cog(Post(bot))
