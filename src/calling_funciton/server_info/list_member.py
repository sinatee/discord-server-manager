import discord
import json

async def list_member(guild: discord.Guild) -> str:
    """list all member in server"""
    members_data = []

    for member in guild.members:
        roles = [role.name for role in member.roles if role.name != "@everyone"]

        members_data.append({
            "id": member.id,
            "name": member.name,
            "display_name": member.display_name,
            "roles": roles,
            "is_bot": member.bot
        })

    return json.dumps(members_data, ensure_ascii=False, indent=2)