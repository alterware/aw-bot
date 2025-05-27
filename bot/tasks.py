from datetime import datetime, timezone
import requests

import discord
from discord.ext import tasks, commands

from bot.utils import aware_utcnow, fetch_api_data
from bot.discourse.handle_request import fetch_cooked_posts, combine_posts_text

from database import migrate_users_with_role

TARGET_DATE = datetime(2036, 8, 12, tzinfo=timezone.utc)
OFFTOPIC_CHANNEL = 1112048063448617142

SPAM_ROLE_ID = 1350511935677927514

COD_GAMES = {
    10180: {"name": "Modern Warfare 2 (2009)", "channel": 1145458108190163014},
    42680: {"name": "Modern Warfare 3 (2011)", "channel": 1145459504436220014},
    209160: {"name": "Call of Duty: Ghosts", "channel": 1145469106133401682},
    209650: {"name": "Call of Duty: Advanced Warfare", "channel": 1145469136919613551},
    311210: {"name": "Call of Duty: Black Ops 3", "channel": 1180796251529293844},
}

DEMENTIA_URL = "https://cdn.discordapp.com/attachments/1112048063448617142/1376956468628291604/share-if-you-have-dementia-v0-cyogps8ikcsc1.jpg"


async def migrate_all_users(bot):
    # Fetch users with the SPAM_ROLE_ID and migrate them to the database
    guild = discord.utils.get(bot.guilds)
    if guild:
        spam_role = discord.utils.get(guild.roles, id=SPAM_ROLE_ID)
        if spam_role:
            for member in spam_role.members:
                migrate_users_with_role(member.id, SPAM_ROLE_ID, member.name)


class SteamSaleChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_steam_sale.start()  # Start the task when the cog is loaded

    def cog_unload(self):
        self.check_steam_sale.cancel()  # Stop the task when the cog is unloaded

    @tasks.loop(hours=24)
    async def check_steam_sale(self):

        for app_id, game_data in COD_GAMES.items():
            game_name = game_data["name"]
            channel_id = game_data["channel"]

            channel = self.bot.get_channel(channel_id)
            if channel is None:
                print(f"Error: Channel ID {channel_id} for {game_name} not found.")
                return

            steam_api_url = (
                f"https://store.steampowered.com/api/appdetails?appids={app_id}"
            )

            try:
                response = requests.get(steam_api_url)
                data = response.json().get(str(app_id), {}).get("data", {})

                if not data:
                    print(f"Warning: No data returned for {game_name}. Skipping...")
                    return

                price_info = data.get("price_overview", {})
                header_image = data.get("header_image", None)

                if not price_info:
                    embed = discord.Embed(
                        title=game_name,
                        description="{game_name} is currently unavailable for purchase.",
                        color=discord.Color.red(),
                    )
                    embed.set_thumbnail(url=header_image if header_image else "")
                    await channel.send(embed=embed)

                    return

                original_price = price_info.get("initial", 0) / 100
                discounted_price = price_info.get("final", 0) / 100
                discount_percent = price_info.get("discount_percent", 0)
                store_url = f"https://store.steampowered.com/app/{app_id}/"

                if discount_percent > 0:
                    embed = discord.Embed(
                        title=f"{game_name} is on Sale!",
                        description=f"-{discount_percent}% OFF!",
                        color=discord.Color.green(),
                    )

                    embed.set_thumbnail(url=header_image if header_image else "")
                    embed.add_field(
                        name="Original Price",
                        value=f"~~${original_price:.2f}~~",
                        inline=True,
                    )
                    embed.add_field(
                        name="Discounted Price",
                        value=f"**${discounted_price:.2f}**",
                        inline=True,
                    )
                    embed.add_field(
                        name="Steam Store",
                        value=f"[View on Steam]({store_url})",
                        inline=False,
                    )
                    await channel.send(embed=embed)

            except requests.RequestException as e:
                print(f"Error fetching Steam sale data for {game_name}: {e}")

    @check_steam_sale.before_loop
    async def before_check_steam_sale(self):
        await self.bot.wait_until_ready()


class DiscourseUpdater(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_discourse_data.start()  # Start the task when the cog is loaded

    def cog_unload(self):
        self.update_discourse_data.cancel()  # Stop the task when the cog is unloaded

    @tasks.loop(hours=6)
    async def update_discourse_data(self):
        """
        Periodically fetches and updates Discourse data for the bot.
        """
        tag_name = "docs"
        print("Fetching Discourse data...")
        cooked_posts = fetch_cooked_posts(tag_name)
        if cooked_posts:
            combined_text = combine_posts_text(
                [{"cooked": post} for post in cooked_posts]
            )
            self.bot.ai_helper.set_discourse_data(combined_text)
            print("Discourse data updated successfully.")
        else:
            print(f"No posts found for tag '{tag_name}'.")

    @update_discourse_data.before_loop
    async def before_update_discourse_data(self):
        await self.bot.wait_until_ready()


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

    @tasks.loop(hours=24)
    async def share_dementia_image():
        channel = bot.get_channel(OFFTOPIC_CHANNEL)
        if channel:
            for _ in range(3):
                await channel.send(DEMENTIA_URL)
        else:
            print("Debug: Channel not found. Check the OFFTOPIC_CHANNEL variable.")

    await migrate_all_users(bot)

    update_status.start()
    heat_death.start()
    share_dementia_image.start()

    await bot.add_cog(SteamSaleChecker(bot))
    await bot.add_cog(DiscourseUpdater(bot))

    print("Tasks extension loaded!")
