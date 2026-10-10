import discord
import json

async def list_member(guild: discord.Guild) -> str:
    """list all member in server"""
    members_data = []


    for member in guild.members:

        print(member.roles)
        roles = [role.name for role in member.roles]

        members_data.append({
            "id": member.id,
            "name": member.name,
            "display_name": member.display_name,
            "roles": roles,
            "is_bot": member.bot
        })

    return json.dumps(members_data, ensure_ascii=False, indent=2)