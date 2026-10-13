from bot import bot
from calling_funciton.server_info.list_role import list_member

async def list_member_tool(guild_id: str) -> str:
    """List all members in a Discord server along with their IDs, names, and roles.
    
    Args:
        guild_id: The ID of the target Discord server (guild).
    """
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return f"Error: Guild {guild_id} not found."
    return await list_member(guild)