from bot.events_handlers import (
    handle_bulk_message_delete,
    handle_member_join,
    handle_member_update,
    handle_message,
    handle_message_delete,
    handle_message_edit,
    handle_reaction_add,
    handle_voice_state_update,
)


async def setup(bot):
    @bot.event
    async def on_message(message):
        await handle_message(message, bot)

    @bot.event
    async def on_reaction_add(reaction, user):
        await handle_reaction_add(reaction, user, bot)

    @bot.event
    async def on_member_join(member):
        await handle_member_join(member)

    @bot.event
    async def on_member_update(before, after):
        await handle_member_update(before, after)

    @bot.event
    async def on_message_delete(message):
        await handle_message_delete(message, bot)

    @bot.event
    async def on_bulk_message_delete(messages):
        await handle_bulk_message_delete(messages, bot)

    @bot.event
    async def on_message_edit(before, after):
        await handle_message_edit(before, after, bot)

    @bot.event
    async def on_voice_state_update(member, before, after):
        await handle_voice_state_update(member, before, after, bot)

    print("Events extension loaded!")
