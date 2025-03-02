from datetime import datetime, timezone

import discord
from discord.ext import tasks

from bot.utils import aware_utcnow, fetch_api_data

TARGET_DATE = datetime(2036, 8, 12, tzinfo=timezone.utc)
OFFTOPIC_CHANNEL = 1112048063448617142


async def setup(bot):
    @tasks.loop(minutes=10)
    async def update_status():
        data = fetch_api_data()
        countPlayers = data.get("countPlayers", 0)
        countServers = data.get("countServers", 0)
        activity = discord.Game(
            name=f"with {countPlayers} players on {countServers} servers"
        )
        await bot.change_presence(activity=activity)

    @tasks.loop(minutes=10080)
    async def heat_death():
        try:
            now = aware_utcnow()

            remaining_seconds = int((TARGET_DATE - now).total_seconds())

            print(f"Seconds until August 12, 2036, UTC: {remaining_seconds}")

            channel = bot.get_channel(OFFTOPIC_CHANNEL)
            if channel:
                await channel.send(
                    f"Can you believe it? Only {remaining_seconds} seconds until August 12th, 2036, the heat death of the universe."
                )
            else:
                print("Debug: Channel not found. Check the OFFTOPIC_CHANNEL variable.")
        except Exception as e:
            print(f"An error occurred in heat_death task: {e}")

    update_status.start()
    heat_death.start()

    print("Tasks extension loaded!")
