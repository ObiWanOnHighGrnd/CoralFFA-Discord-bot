"""
Copyright © Krypton 2019-Present - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized Discord bot in Python

Version: 6.5.0
"""

import runpy
import os
from datetime import datetime
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context


CORAL_BLUE = 0x5BC8E8
CORAL_ERROR = 0xE02B2B

MODERATION_ROLES_FILE = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "moderation_roles.py"
)


def load_command_roles():
    if not MODERATION_ROLES_FILE.exists():
        return {}

    try:
        config = runpy.run_path(str(MODERATION_ROLES_FILE))
        data = config.get("COMMAND_ROLES", {})
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError, SyntaxError):
        return {}


def command_role_required(command_name):
    async def predicate(context):
        if context.guild is None:
            return False

        if await context.bot.is_owner(context.author):
            return True

        role_data = load_command_roles()
        configured_ids = role_data.get(command_name, [])

        try:
            allowed_role_ids = {int(role_id) for role_id in configured_ids}
        except (TypeError, ValueError):
            return False

        return any(
            role.id in allowed_role_ids
            for role in getattr(context.author, "roles", [])
        )

    return commands.check(predicate)


class Moderation(commands.Cog, name="moderation"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="kick",
        description="Kick a user out of the server.",
    )
    @command_role_required("kick")
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(
        user="The user that should be kicked.",
        reason="The reason why the user should be kicked.",
    )
    async def kick(
        self, context: Context, user: discord.User, *, reason: str = "Not specified"
    ) -> None:
        """
        Kick a user out of the server.

        :param context: The hybrid command context.
        :param user: The user that should be kicked from the server.
        :param reason: The reason for the kick. Default is "Not specified".
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        if member.guild_permissions.administrator:
            embed = discord.Embed(
                description="User has administrator permissions.", color=0xE02B2B
            )
            await context.send(embed=embed)
        else:
            try:
                embed = discord.Embed(
                    description=f"**{member}** was kicked by **{context.author}**!",
                    color=0x5BC8E8,
                )
                embed.add_field(name="Reason:", value=reason)
                await context.send(embed=embed)
                try:
                    await member.send(
                        f"You were kicked by **{context.author}** from **{context.guild.name}**!\nReason: {reason}"
                    )
                except:
                    # Couldn't send a message in the private messages of the user
                    pass
                await member.kick(reason=reason)
            except:
                embed = discord.Embed(
                    description="An error occurred while trying to kick the user. Make sure my role is above the role of the user you want to kick.",
                    color=0xE02B2B,
                )
                await context.send(embed=embed)

    @commands.hybrid_command(
        name="nick",
        description="Change the nickname of a user on a server.",
    )
    @command_role_required("nick")
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.describe(
        user="The user that should have a new nickname.",
        nickname="The new nickname that should be set.",
    )
    async def nick(
        self, context: Context, user: discord.User, *, nickname: str = None
    ) -> None:
        """
        Change the nickname of a user on a server.

        :param context: The hybrid command context.
        :param user: The user that should have its nickname changed.
        :param nickname: The new nickname of the user. Default is None, which will reset the nickname.
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        try:
            await member.edit(nick=nickname)
            embed = discord.Embed(
                description=f"**{member}'s** new nickname is **{nickname}**!",
                color=0x5BC8E8,
            )
            await context.send(embed=embed)
        except:
            embed = discord.Embed(
                description="An error occurred while trying to change the nickname of the user. Make sure my role is above the role of the user you want to change the nickname.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="ban",
        description="Bans a user from the server.",
    )
    @command_role_required("ban")
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(
        user="The user that should be banned.",
        reason="The reason why the user should be banned.",
    )
    async def ban(
        self, context: Context, user: discord.User, *, reason: str = "Not specified"
    ) -> None:
        """
        Bans a user from the server.

        :param context: The hybrid command context.
        :param user: The user that should be banned from the server.
        :param reason: The reason for the ban. Default is "Not specified".
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        try:
            if member.guild_permissions.administrator:
                embed = discord.Embed(
                    description="User has administrator permissions.", color=0xE02B2B
                )
                await context.send(embed=embed)
            else:
                embed = discord.Embed(
                    description=f"**{member}** was banned by **{context.author}**!",
                    color=0x5BC8E8,
                )
                embed.add_field(name="Reason:", value=reason)
                await context.send(embed=embed)
                try:
                    await member.send(
                        f"You were banned by **{context.author}** from **{context.guild.name}**!\nReason: {reason}"
                    )
                except:
                    # Couldn't send a message in the private messages of the user
                    pass
                await member.ban(reason=reason)
        except:
            embed = discord.Embed(
                title="Error!",
                description="An error occurred while trying to ban the user. Make sure my role is above the role of the user you want to ban.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="warn",
        description="Add a warning to a user.",
    )
    @command_role_required("warn")
    @app_commands.describe(
        user="The user that should be warned.",
        reason="The reason for the warning.",
    )
    async def warn(
        self,
        context: Context,
        user: discord.User,
        *,
        reason: str = "Not specified",
    ) -> None:
        member = context.guild.get_member(user.id)
        if member is None:
            member = await context.guild.fetch_member(user.id)

        total = await self.bot.database.add_warn(
            user.id,
            context.guild.id,
            context.author.id,
            reason,
        )

        dm_sent = True
        try:
            await member.send(
                f"You were warned by **{context.author}** "
                f"in **{context.guild.name}**!\nReason: {reason}"
            )
        except (discord.Forbidden, discord.HTTPException):
            dm_sent = False

        embed = discord.Embed(
            description=(
                f"**{member}** was warned by **{context.author}**!\n"
                f"Total warnings: **{total}**"
            ),
            color=0x5BC8E8,
        )
        embed.add_field(name="Reason", value=reason, inline=False)

        if not dm_sent:
            embed.set_footer(text="The user could not be notified by DM.")

        await context.send(embed=embed)

    @commands.hybrid_command(
        name="warns",
        description="Show all warned users or one user's warning history.",
    )
    @command_role_required("warns")
    @app_commands.describe(
        user="Optional: show the full warnings for this user."
    )
    async def warns(
        self,
        context: Context,
        user: discord.User = None,
    ) -> None:
        if user is not None:
            warnings_list = await self.bot.database.get_warnings(
                user.id,
                context.guild.id,
            )

            embed = discord.Embed(
                title=f"Warnings for {user}",
                color=0x5BC8E8,
            )

            if not warnings_list:
                embed.description = "This user has no warnings."
            else:
                lines = []
                for warning in warnings_list:
                    lines.append(
                        f"• Warned by <@{warning[2]}>: "
                        f"**{warning[3]}** "
                        f"(<t:{warning[4]}>) — ID `#{warning[5]}`"
                    )

                description = "\n".join(lines)
                embed.description = description[:4096]

            await context.send(embed=embed)
            return

        warned_users = []

        for member in context.guild.members:
            warnings_list = await self.bot.database.get_warnings(
                member.id,
                context.guild.id,
            )

            if warnings_list:
                warned_users.append((member, len(warnings_list)))

        warned_users.sort(key=lambda item: item[1], reverse=True)

        embed = discord.Embed(
            title="Server warnings",
            color=0x5BC8E8,
        )

        if not warned_users:
            embed.description = "Nobody in this server has any warnings."
        else:
            lines = []
            for member, warning_count in warned_users:
                label = "warning" if warning_count == 1 else "warnings"
                lines.append(
                    f"• {member.mention} — **{warning_count} {label}**"
                )

            description = "\n".join(lines)
            embed.description = description[:4096]
            embed.set_footer(
                text=f"{len(warned_users)} warned user(s)"
            )

        await context.send(embed=embed)

    @commands.hybrid_command(
        name="unwarn",
        description="Remove one warning from a user by warning ID.",
    )
    @command_role_required("unwarn")
    @app_commands.describe(
        user="The user whose warning should be removed.",
        warn_id="The warning ID to remove.",
    )
    async def unwarn(
        self,
        context: Context,
        user: discord.User,
        warn_id: int,
    ) -> None:
        member = context.guild.get_member(user.id)
        if member is None:
            member = await context.guild.fetch_member(user.id)

        total = await self.bot.database.remove_warn(
            warn_id,
            user.id,
            context.guild.id,
        )

        embed = discord.Embed(
            description=(
                f"Removed warning `#{warn_id}` from **{member}**.\n"
                f"Total warnings: **{total}**"
            ),
            color=0x5BC8E8,
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="clearwarns",
        description="Remove every warning from a user.",
    )
    @command_role_required("clearwarns")
    @app_commands.describe(
        user="The user whose warnings should all be removed.",
    )
    async def clearwarns(
        self,
        context: Context,
        user: discord.User,
    ) -> None:
        warnings_list = await self.bot.database.get_warnings(
            user.id,
            context.guild.id,
        )

        if not warnings_list:
            await context.send(f"**{user}** has no warnings to clear.")
            return

        removed = 0
        for warning in warnings_list:
            await self.bot.database.remove_warn(
                warning[5],
                user.id,
                context.guild.id,
            )
            removed += 1

        label = "warning" if removed == 1 else "warnings"
        embed = discord.Embed(
            description=(
                f"Cleared **{removed} {label}** from **{user}** "
                f"by **{context.author}**."
            ),
            color=0x5BC8E8,
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="purge",
        description="Delete a number of messages.",
    )
    @command_role_required("purge")
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="The amount of messages that should be deleted.")
    async def purge(self, context: Context, amount: int) -> None:
        """
        Delete a number of messages.

        :param context: The hybrid command context.
        :param amount: The number of messages that should be deleted.
        """
        if amount < 1:
            await context.send(
                "The amount must be at least 1.",
                ephemeral=context.interaction is not None,
            )
            return

        if context.interaction is not None:
            await context.defer()
            purged_messages = await context.channel.purge(limit=amount)
        else:
            # Delete the prefix command itself, then delete the requested number
            # of additional messages.
            try:
                await context.message.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

            purged_messages = await context.channel.purge(limit=amount)

        deleted_count = len(purged_messages)
        noun = "message" if deleted_count == 1 else "messages"

        author_counts = {}
        for deleted_message in purged_messages:
            author = deleted_message.author
            current = author_counts.get(author.id, {"name": str(author), "count": 0})
            current["count"] += 1
            author_counts[author.id] = current

        breakdown_lines = []
        for data in sorted(
            author_counts.values(),
            key=lambda item: item["count"],
            reverse=True,
        ):
            count = data["count"]
            label = "message" if count == 1 else "messages"
            breakdown_lines.append(
                f"**{data['name']}** — {count} {label}"
            )

        breakdown = "\n".join(breakdown_lines) if breakdown_lines else "No messages deleted."

        embed = discord.Embed(
            title="Purge complete",
            description=(
                f"Purged by **{context.author}**\n"
                f"Cleared **{deleted_count}** {noun}.\n\n"
                f"{breakdown}"
            ),
            color=0x5BC8E8,
        )
        await context.send(embed=embed, delete_after=2)

    @commands.hybrid_command(
        name="hackban",
        description="Bans a user without the user having to be in the server.",
    )
    @command_role_required("hackban")
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(
        user_id="The user ID that should be banned.",
        reason="The reason why the user should be banned.",
    )
    async def hackban(
        self, context: Context, user_id: str, *, reason: str = "Not specified"
    ) -> None:
        """
        Bans a user without the user having to be in the server.

        :param context: The hybrid command context.
        :param user_id: The ID of the user that should be banned.
        :param reason: The reason for the ban. Default is "Not specified".
        """
        try:
            await self.bot.http.ban(user_id, context.guild.id, reason=reason)
            user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(
                int(user_id)
            )
            embed = discord.Embed(
                description=f"**{user}** (ID: {user_id}) was banned by **{context.author}**!",
                color=0x5BC8E8,
            )
            embed.add_field(name="Reason:", value=reason)
            await context.send(embed=embed)
        except Exception:
            embed = discord.Embed(
                description="An error occurred while trying to ban the user. Make sure ID is an existing ID that belongs to a user.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="lock",
        description="Lock the current channel.",
    )
    @command_role_required("lock")
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.describe(reason="Optional reason for locking the channel.")
    async def lock(
        self,
        context: Context,
        *,
        reason: str = "Not specified",
    ) -> None:
        channel = context.channel
        if not isinstance(channel, discord.TextChannel):
            await context.send("This command only works in text channels.")
            return

        overwrite = channel.overwrites_for(context.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(
            context.guild.default_role,
            overwrite=overwrite,
            reason=f"Locked by {context.author}: {reason}",
        )

        embed = discord.Embed(
            description=(
                f"🔒 {channel.mention} was locked by **{context.author}**.\n"
                f"Reason: {reason}"
            ),
            color=0x5BC8E8,
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="unlock",
        description="Unlock the current channel.",
    )
    @command_role_required("unlock")
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, context: Context) -> None:
        channel = context.channel
        if not isinstance(channel, discord.TextChannel):
            await context.send("This command only works in text channels.")
            return

        overwrite = channel.overwrites_for(context.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(
            context.guild.default_role,
            overwrite=overwrite,
            reason=f"Unlocked by {context.author}",
        )

        embed = discord.Embed(
            description=(
                f"🔓 {channel.mention} was unlocked by **{context.author}**."
            ),
            color=0x5BC8E8,
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="archive",
        description="Archives in a text file the last messages with a chosen limit of messages.",
    )
    @command_role_required("archive")
    @app_commands.describe(
        limit="The limit of messages that should be archived.",
    )
    async def archive(self, context: Context, limit: int = 10) -> None:
        """
        Archives in a text file the last messages with a chosen limit of messages. This command requires the MESSAGE_CONTENT intent to work properly.

        :param limit: The limit of messages that should be archived. Default is 10.
        """
        log_file = f"{context.channel.id}.log"
        with open(log_file, "w", encoding="UTF-8") as f:
            f.write(
                f'Archived messages from: #{context.channel} ({context.channel.id}) in the guild "{context.guild}" ({context.guild.id}) at {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}\n'
            )
            async for message in context.channel.history(
                limit=limit, before=context.message
            ):
                attachments = []
                for attachment in message.attachments:
                    attachments.append(attachment.url)
                attachments_text = (
                    f"[Attached File{'s' if len(attachments) >= 2 else ''}: {', '.join(attachments)}]"
                    if len(attachments) >= 1
                    else ""
                )
                f.write(
                    f"{message.created_at.strftime('%d.%m.%Y %H:%M:%S')} {message.author} {message.id}: {message.clean_content} {attachments_text}\n"
                )
        f = discord.File(log_file)
        await context.send(file=f)
        os.remove(log_file)


    async def cog_command_error(
        self,
        context: Context,
        error: commands.CommandError,
    ) -> None:
        original = getattr(error, "original", error)

        if isinstance(original, commands.NotOwner):
            await context.send(
                "Only the bot owner can use that command.",
                ephemeral=context.interaction is not None,
            )
            return

        if isinstance(original, commands.CheckFailure):
            await context.send(
                "You do not have a role authorised for this command.",
                ephemeral=context.interaction is not None,
            )
            return

        raise error


async def setup(bot) -> None:
    await bot.add_cog(Moderation(bot))
