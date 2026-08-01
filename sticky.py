import asyncio
import json
from pathlib import Path
from typing import Dict, Optional, Union

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context


class Sticky(commands.Cog, name="sticky"):
    """Persistent sticky messages for text channels."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.data_path = Path(__file__).resolve().parent.parent / "data" / "sticky_messages.json"
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.stickies: Dict[str, Dict[str, object]] = self._load_data()
        self.channel_locks: Dict[int, asyncio.Lock] = {}
        self.bot.logger.info("Sticky message cog initialised.")

    def _load_data(self) -> Dict[str, Dict[str, object]]:
        if not self.data_path.exists():
            return {}

        try:
            with self.data_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_data(self) -> None:
        temporary_path = self.data_path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(self.stickies, file, indent=2, ensure_ascii=False)
        temporary_path.replace(self.data_path)

    @staticmethod
    def _make_embed(message: str) -> discord.Embed:
        return discord.Embed(
            title="**Stickied Message:**",
            description=message,
            color=0x5BC8E8,
        )

    async def _delete_previous(
        self,
        channel: Union[discord.TextChannel, discord.Thread],
        message_id: Optional[int],
    ) -> None:
        if not message_id:
            return

        try:
            previous = await channel.fetch_message(message_id)
            await previous.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    async def _post_sticky(
        self,
        channel: Union[discord.TextChannel, discord.Thread],
        content: str,
    ) -> discord.Message:
        return await channel.send(embed=self._make_embed(content))

    @commands.hybrid_command(
        name="sticky",
        description="Create or replace the sticky message in this channel.",
    )
    @app_commands.describe(message="The message that should remain at the bottom of this channel.")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def sticky(self, context: Context, *, message: str) -> None:
        if len(message) > 4096:
            await context.send(
                "The sticky message must be 4,096 characters or fewer.",
                ephemeral=context.interaction is not None,
            )
            return

        channel = context.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            await context.send(
                "Sticky messages can only be used in text channels or threads.",
                ephemeral=context.interaction is not None,
            )
            return

        channel_key = str(channel.id)
        existing = self.stickies.get(channel_key, {})
        previous_id = existing.get("message_id")
        if isinstance(previous_id, int):
            await self._delete_previous(channel, previous_id)

        sticky_message = await self._post_sticky(channel, message)
        self.stickies[channel_key] = {
            "guild_id": context.guild.id,
            "channel_id": channel.id,
            "content": message,
            "message_id": sticky_message.id,
        }
        self._save_data()

        await context.send(
            "Sticky message set.",
            ephemeral=context.interaction is not None,
            delete_after=None if context.interaction is not None else 5,
        )

    @commands.hybrid_command(
        name="unsticky",
        description="Remove the sticky message from this channel.",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def unsticky(self, context: Context) -> None:
        channel = context.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return

        channel_key = str(channel.id)
        existing = self.stickies.pop(channel_key, None)

        if existing is None:
            await context.send(
                "There is no sticky message in this channel.",
                ephemeral=context.interaction is not None,
            )
            return

        previous_id = existing.get("message_id")
        if isinstance(previous_id, int):
            await self._delete_previous(channel, previous_id)

        self._save_data()
        await context.send(
            "Sticky message removed.",
            ephemeral=context.interaction is not None,
            delete_after=None if context.interaction is not None else 5,
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return

        channel = message.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return

        channel_key = str(channel.id)
        sticky_data = self.stickies.get(channel_key)
        if sticky_data is None:
            return

        # Let prefix commands complete before moving the sticky.
        await asyncio.sleep(1)

        lock = self.channel_locks.setdefault(channel.id, asyncio.Lock())
        async with lock:
            current_data = self.stickies.get(channel_key)
            if current_data is None:
                return

            content = current_data.get("content")
            if not isinstance(content, str) or not content:
                return

            previous_id = current_data.get("message_id")
            if isinstance(previous_id, int):
                await self._delete_previous(channel, previous_id)

            try:
                new_message = await self._post_sticky(channel, content)
            except discord.Forbidden:
                self.bot.logger.error(
                    f"Cannot post sticky message in channel {channel.id}: "
                    "missing Send Messages or Embed Links permission."
                )
                return
            except discord.HTTPException as error:
                self.bot.logger.error(
                    f"Failed to repost sticky message in channel {channel.id}: {error}"
                )
                return

            current_data["message_id"] = new_message.id
            self._save_data()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Sticky(bot))
