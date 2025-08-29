import asyncio

import discord

MP3_PATH = "sounds/hello.mp3"


async def handle_voice_state_update(member, before, after, bot):
    # Ignore bot users
    if member.bot:
        return

    # Check if the member joined a new voice channel
    if after.channel and (before.channel != after.channel):
        voice_channel = after.channel

        try:
            # Join the voice channel
            vc = await voice_channel.connect()

            # Play the MP3 file
            vc.play(discord.FFmpegPCMAudio(MP3_PATH))

            # Wait for playback to finish
            while vc.is_playing():
                await asyncio.sleep(1)

            # Disconnect
            await vc.disconnect()

        except Exception as e:
            print(f"Error: {e}")
