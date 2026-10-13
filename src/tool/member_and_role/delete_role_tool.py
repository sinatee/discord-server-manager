from bot import bot
from calling_funciton.member_and_role.delete_role import delete_role

async def delete_role_tool(guild_id: str, role_id: str) -> str:
    """Delete an existing role from a Discord server by its role ID.
    
    Args:
        guild_id: The ID of the target Discord server (guild).
        role_id: The ID of the role to delete.
    """
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return "Error: Guild not found."
    return await delete_role(guild, role_id)