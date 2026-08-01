import os

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

CORAL_BLUE = 0x5BC8E8


class Welcome(commands.Cog, name="welcome"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.bot.logger.info("Welcome cog loaded.")

    def get_welcome_channel(self, guild: discord.Guild):
        channel_id = os.getenv("WELCOME_CHANNEL_ID")
        if channel_id:
            try:
                channel = guild.get_channel(int(channel_id))
                if channel is not None:
                    return channel
            except ValueError:
                self.bot.logger.error("WELCOME_CHANNEL_ID must contain only numbers.")
        return guild.system_channel

    async def send_welcome(self, member: discord.Member) -> bool:
        channel = self.get_welcome_channel(member.guild)
        if channel is None:
            self.bot.logger.error(
                "No valid welcome channel found in %s.", member.guild.name
            )
            return False

        embed = discord.Embed(
            title="Welcome to CoralFFA! 🪸",
            description=(
                f"Welcome {member.mention}!\n\n"
                "Read the rules, hop in a match, and enjoy your stay."
            ),
            color=CORAL_BLUE,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name="Member count",
            value=f"You are member **#{member.guild.member_count}**",
            inline=False,
        )
        embed.set_footer(text=f"CoralFFA • {member.guild.name}")

        try:
            await channel.send(content=member.mention, embed=embed)
        except discord.Forbidden:
            self.bot.logger.error(
                "Missing Send Messages or Embed Links permission in welcome channel %s.",
                channel.id,
            )
            return False
        except discord.HTTPException as error:
            self.bot.logger.error("Welcome message failed: %s", error)
            return False

        self.bot.logger.info(
            "Welcome message sent for %s in #%s.",
            member,
            getattr(channel, "name", channel.id),
        )
        return True

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        self.bot.logger.info("Member join event received for %s.", member)
        await self.send_welcome(member)

    @commands.hybrid_command(
        name="testwelcome",
        description="Test the welcome message in the configured channel.",
    )
    @commands.is_owner()
    @app_commands.describe(user="Optional member to use in the test welcome.")
    async def testwelcome(
        self,
        context: Context,
        user: discord.Member = None,
    ) -> None:
        member = user or context.author
        success = await self.send_welcome(member)
        await context.send(
            "Welcome test sent." if success else "Welcome test failed. Check the console.",
            ephemeral=context.interaction is not None,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Welcome(bot))
