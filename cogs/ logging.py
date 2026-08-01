from datetime import datetime

import discord
from discord.ext import commands

CORAL_BLUE = 0x5BC8E8
LOG_CHANNEL_ID = 1529486448619815174


class Logging(commands.Cog, name="logging"):
    """Logs completed moderation commands only."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        if hasattr(self.bot, "logger"):
            self.bot.logger.info(
                "Moderation logging cog initialised for channel %s.", LOG_CHANNEL_ID
            )

    async def get_log_channel(self):
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel is not None:
            return channel
        try:
            return await self.bot.fetch_channel(LOG_CHANNEL_ID)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    @commands.Cog.listener()
    async def on_command_completion(self, context: commands.Context) -> None:
        if context.guild is None or context.command is None:
            return
        if context.command.cog_name != "moderation":
            return

        channel = await self.get_log_channel()
        if channel is None:
            return

        command_name = context.command.qualified_name

        embed = discord.Embed(
            title="Moderation action — CoralFFA",
            description=(
                f"Moderator: {context.author.mention} "
                f"(`{context.author.id}`)\n"
                f"Channel: {context.channel.mention}\n"
                f"Command: `{command_name}`"
            ),
            color=CORAL_BLUE,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text="CoralFFA Mod Log")

        try:
            await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Logging(bot))
