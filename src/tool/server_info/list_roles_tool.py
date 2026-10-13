from bot import bot
from calling_funciton.server_info.list_role import list_roles

async def list_roles_tool(guild_id: str) -> str:
    """List all roles in a Discord server, ordered from highest to lowest hierarchy.
    
    Args:
        guild_id: The ID of the target Discord server (guild).
    """
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return '{"error": "Guild not found."}'
    return await list_roles(guild)