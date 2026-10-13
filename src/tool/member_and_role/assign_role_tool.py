from bot import bot
from calling_funciton.member_and_role.assign_role import assign_role

async def assign_role_tool(guild_id: str, user_id: str, role_id: str) -> str:
    """Assign a role to a member in a Discord server.
    
    Args:
        guild_id: The ID of the target Discord server (guild).
        user_id: The ID of the member to assign the role to.
        role_id: The ID of the role to assign.
    """
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return "Error: Guild not found."
    return await assign_role(guild, user_id, role_id)