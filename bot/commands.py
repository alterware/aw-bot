import re
from typing import Literal

import discord
from discord import app_commands

from bot.log import logger
from database import (
    get_meme_patterns,
    add_aka_response,
    search_aka,
    add_meme_pattern,
    add_user_to_blacklist,
    is_user_blacklisted,
)

GUILD_ID = 1110531063161299074

BOT_LOG = 1112049391482703873
GENERAL_CHANNEL = 1110531063744303138


async def setup(bot):
    async def on_tree_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            return await interaction.response.send_message(
                f"Command is currently on cooldown! Try again in **{error.retry_after:.2f}** seconds!"
            )
        elif isinstance(error, app_commands.MissingPermissions):
            return await interaction.response.send_message(
                "You are missing permissions to use that"
            )
        else:
            raise error

    bot.tree.on_error = on_tree_error

    @bot.tree.command(
        name="add_aka_message",
        description="Add a new aka message to the database.",
        guild=discord.Object(id=GUILD_ID),
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_aka_message(
        interaction: discord.Interaction, aka: str, response: str
    ):
        """Slash command to add a new aka pattern to the database."""
        add_aka_response(aka, response)
        await interaction.response.send_message(
            f"Pattern added!\n**AKA:** `{aka}`\n**Response:** `{response}`"
        )

    @bot.tree.command(
        name="add_meme_pattern",
        description="Add a new message pattern to the database.",
        guild=discord.Object(id=GUILD_ID),
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_meme_pattern_cmd(
        interaction: discord.Interaction, regex: str, response: str
    ):
        """Slash command to add a new message pattern to the database."""
        add_meme_pattern(regex, response)
        logger.info("Saved a new meme pattern: %s", regex)
        await interaction.response.send_message(
            f"Pattern added!\n**Regex:** `{regex}`\n**Response:** `{response}`"
        )

    @bot.tree.command(
        name="add_to_blacklist",
        description="Add a user to the blacklist.",
        guild=discord.Object(id=GUILD_ID),
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_to_blacklist_cmd(
        interaction: discord.Interaction, user: discord.User, reason: str
    ):
        """Slash command to add a user to the blacklist."""
        add_user_to_blacklist(user.id, reason)
        await interaction.response.send_message(
            f"User **{user.name}** has been added to the blacklist.\n**Reason:** `{reason}`"
        )

    @bot.tree.command(
        name="aka",
        description="Check if the input matches any predefined aka patterns.",
        guild=discord.Object(id=GUILD_ID),
    )
    async def aka(interaction: discord.Interaction, input: str):
        """
        Slash command to check if the input matches any predefined aka patterns.
        """
        # Check if the user is blacklisted
        if is_user_blacklisted(interaction.user.id):
            await interaction.response.send_message(
                "You are blacklisted from using this command.", ephemeral=True
            )
            return

        # Search the database for a match
        response = search_aka(input)

        if response:
            await interaction.response.send_message(response, ephemeral=False)
        else:
            await interaction.response.send_message(
                "No matching aka patterns found.", ephemeral=True
            )

    @bot.tree.command(
        name="meme",
        description="Check if the input matches any predefined memes.",
        guild=discord.Object(id=GUILD_ID),
    )
    async def meme(interaction: discord.Interaction, input: str):
        """
        Slash command to check if the input matches any predefined patterns.
        """
        # Check if the user is blacklisted
        if is_user_blacklisted(interaction.user.id):
            await interaction.response.send_message(
                "You are blacklisted from using this command.", ephemeral=True
            )
            return

        message_patterns = get_meme_patterns()
        # Check if any of the patterns match the input
        for pattern in message_patterns:
            if re.search(pattern["regex"], input, re.IGNORECASE):
                response = pattern["response"]
                reply_message = await interaction.response.send_message(
                    response, ephemeral=False
                )
                # Add a reaction to the reply message (if the user decides to delete it)
                await reply_message.add_reaction("\U0000274c")
                break
        else:
            await interaction.response.send_message(
                "No matching patterns found.", ephemeral=True
            )

    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))  # Force sync

    logger.info("Commands extension loaded!")
