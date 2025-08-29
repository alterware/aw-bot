import discord

from bot.utils import generate_random_nickname, is_numeric_name, is_valid_username
from database import user_has_role

SPAM_ROLE_ID = 1350511935677927514


async def handle_member_join(member):
    name_to_check = member.name

    if member.display_name:
        name_to_check = member.display_name

    if (
        len(name_to_check) < 3
        or not is_valid_username(name_to_check)
        or is_numeric_name(name_to_check)
    ):
        new_nick = generate_random_nickname()
        await member.edit(nick=new_nick)

    if user_has_role(member.id):
        spam_role = discord.utils.get(member.guild.roles, id=SPAM_ROLE_ID)
        if spam_role:
            await member.add_roles(spam_role)


async def handle_member_update(before, after):
    name_to_check = after.name

    if after.nick:
        name_to_check = after.nick

    if (
        len(name_to_check) < 3
        or not is_valid_username(name_to_check)
        or is_numeric_name(name_to_check)
    ):
        new_nick = generate_random_nickname()
        await after.edit(nick=new_nick)
