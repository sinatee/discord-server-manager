from bot import bot
from calling_funciton.member_and_role.unassign_role import unassign_role

async def unassign_role_tool(guild_id: str, user_id: str, role_id: str) -> str:
    """Remove a role from a member in a Discord server.
    
    Args:
        guild_id: The ID of the target Discord server (guild).
        user_id: The ID of the member to remove the role from.
        role_id: The ID of the role to remove.
    """
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return "Error: Guild not found."
    return await unassign_role(guild, user_id, role_id)