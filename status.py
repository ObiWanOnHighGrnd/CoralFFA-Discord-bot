import asyncio
import json
import os
from pathlib import Path
from typing import Optional, Tuple

import aiohttp
import discord
from discord.ext import commands, tasks


MINEKEEP_API = "https://api.minekeep.net/v1/servers"


class Status(commands.Cog, name="status"):
    """Maintains one editable MineKeep server-status message."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self.channel_id = int(os.getenv("STATUS_CHANNEL_ID", "0"))
        self.server_name = os.getenv("MINEKEEP_SERVER_NAME", "coralffa").lower()
        self.update_interval = int(os.getenv("STATUS_UPDATE_INTERVAL", "60"))

        self.data_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "status_message_id.json"
        )
        self.data_path.parent.mkdir(parents=True, exist_ok=True)

        self.update_status.change_interval(seconds=self.update_interval)
        self.update_status.start()

        if hasattr(self.bot, "logger"):
            self.bot.logger.info("Status cog initialised.")

    def cog_unload(self) -> None:
        self.update_status.cancel()

    async def get_server_status(self) -> Tuple[Optional[bool], Optional[int]]:
        """
        Return:
        - (True, player_count) when online
        - (False, 0) when not listed
        - (None, None) when the API could not be checked
        """
        timeout = aiohttp.ClientTimeout(total=10)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(MINEKEEP_API) as response:
                    response.raise_for_status()
                    payload = await response.json()
        except (
            aiohttp.ClientError,
            asyncio.TimeoutError,
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            if hasattr(self.bot, "logger"):
                self.bot.logger.error(
                    "MineKeep API request failed: %s",
                    error,
                )
            return None, None

        servers = payload.get("servers", [])

        match = next(
            (
                server
                for server in servers
                if self.server_name
                in str(server.get("name", "")).lower()
            ),
            None,
        )

        if match is None:
            return False, 0

        try:
            player_count = int(
                match.get("players", {}).get("online", 0)
            )
        except (TypeError, ValueError):
            player_count = 0

        return True, player_count

    def build_embed(
        self,
        is_online: Optional[bool],
        player_count: Optional[int],
    ) -> discord.Embed:
        if is_online is None:
            embed = discord.Embed(
                title="CoralFFA Status",
                description="⚠️ Couldn't reach MineKeep's API right now.",
                color=discord.Color.orange(),
            )
        elif is_online:
            embed = discord.Embed(
                title="CoralFFA Status",
                description="🟢 **Online**",
                color=discord.Color.green(),
            )
            embed.add_field(
                name="Players",
                value=str(player_count or 0),
                inline=False,
            )
        else:
            embed = discord.Embed(
                title="CoralFFA Status",
                description="🔴 **Offline**",
                color=discord.Color.red(),
            )

        embed.set_footer(
            text="Updates every {}s".format(self.update_interval)
        )
        return embed

    def load_message_id(self) -> Optional[int]:
        if not self.data_path.exists():
            return None

        try:
            with self.data_path.open("r", encoding="utf-8") as file:
                value = json.load(file).get("message_id")
            return int(value) if value else None
        except (
            OSError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ):
            return None

    def save_message_id(self, message_id: int) -> None:
        temporary_path = self.data_path.with_suffix(".tmp")

        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump({"message_id": message_id}, file)

        temporary_path.replace(self.data_path)

    @tasks.loop(seconds=60)
    async def update_status(self) -> None:
        if not self.channel_id:
            if hasattr(self.bot, "logger"):
                self.bot.logger.error(
                    "STATUS_CHANNEL_ID is missing or invalid."
                )
            return

        channel = self.bot.get_channel(self.channel_id)

        if channel is None:
            try:
                channel = await self.bot.fetch_channel(self.channel_id)
            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException,
            ) as error:
                if hasattr(self.bot, "logger"):
                    self.bot.logger.error(
                        "Could not find status channel %s: %s",
                        self.channel_id,
                        error,
                    )
                return

        is_online, player_count = await self.get_server_status()
        embed = self.build_embed(is_online, player_count)

        message = None
        message_id = self.load_message_id()

        if message_id:
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                message = None
            except (
                discord.Forbidden,
                discord.HTTPException,
            ) as error:
                if hasattr(self.bot, "logger"):
                    self.bot.logger.error(
                        "Could not fetch status message: %s",
                        error,
                    )
                return

        try:
            if message is not None:
                await message.edit(embed=embed)
            else:
                new_message = await channel.send(embed=embed)
                self.save_message_id(new_message.id)
        except discord.Forbidden:
            if hasattr(self.bot, "logger"):
                self.bot.logger.error(
                    "Missing Send Messages or Embed Links permission "
                    "in the status channel."
                )
        except discord.HTTPException as error:
            if hasattr(self.bot, "logger"):
                self.bot.logger.error(
                    "Could not update status message: %s",
                    error,
                )

    @update_status.before_loop
    async def before_update_status(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Status(bot))
