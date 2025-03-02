from typing import Literal

import discord
from discord import app_commands

from bot.utils import compile_stats, fetch_game_stats, perform_search

GUILD_ID = 1110531063161299074


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
        name="search",
        description="Search for servers by hostname or IP.",
        guild=discord.Object(id=GUILD_ID),
    )
    async def slash_search(interaction: discord.Interaction, query: str):
        results = await perform_search(query)
        await interaction.response.send_message(results)

    @app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id, i.user.id))
    @bot.tree.command(
        name="stats",
        description="Get stats for a specific game or all games",
        guild=discord.Object(id=GUILD_ID),
    )
    async def stats(
        interaction: discord.Interaction, game: Literal["iw4", "s1", "iw6", "t7", "all"]
    ):
        if game == "all":
            stats_message = await compile_stats()
        else:
            data = await fetch_game_stats(game)
            if data:
                stats_message = f"**Stats for {game.upper()}:**\n"
                count_servers = data.get("countServers", "N/A")
                count_players = data.get("countPlayers", "N/A")
                stats_message += f"Total Servers: {count_servers}\n"
                stats_message += f"Total Players: {count_players}\n"
            else:
                stats_message = "Failed to fetch game stats. Please try again later."

        await interaction.response.send_message(stats_message, ephemeral=True)

    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))  # Force sync

    print("Commands extension loaded!")
