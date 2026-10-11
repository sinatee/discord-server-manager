import json
import discord

async def list_roles(guild: discord.Guild) -> str:
    """List all roles in the server ordered from highest to lowest hierarchy as JSON."""
    if not guild:
        return json.dumps({"error": "Guild not found."})

    roles_data = []
    # Reversed so top hierarchy comes first
    for role in reversed(guild.roles):
        roles_data.append({
            "id": str(role.id),
            "name": role.name,
            "color": str(role.color) if role.color.value != 0 else None,
            "hoist": role.hoist,
            "position": role.position,
            "member_count": len(role.members),
            "is_bot_managed": role.is_bot_managed()
        })

    return json.dumps(roles_data, ensure_ascii=False, indent=2)