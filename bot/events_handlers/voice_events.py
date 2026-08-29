import asyncio

import discord

from bot.log import logger

MP3_PATH = "sounds/hello.mp3"
_locks: dict[int, asyncio.Lock] = {}


async def handle_voice_state_update(member, before, after, bot):
    if member.bot:
        return

    if after.channel and (before.channel != after.channel):
        voice_channel = after.channel
        guild_id = voice_channel.guild.id
        lock = _locks.setdefault(guild_id, asyncio.Lock())

        if lock.locked():
            return  # a connect for this guild is already in flight

        async with lock:
            # bail if we're already connected to this guild's voice
            if voice_channel.guild.voice_client is not None:
                return
            try:
                vc = await voice_channel.connect()
                vc.play(discord.FFmpegPCMAudio(MP3_PATH))
                while vc.is_playing():
                    await asyncio.sleep(1)
                await vc.disconnect()
            except Exception as e:
                logger.error("Error while connecting to a voice channel: %s", e)
