from bot import bot
from calling_funciton.server_info.list_category import list_category

async def list_category_tool(guild_id: str) -> str:
    """List all categories in a Discord server.
    
    Args:
        guild_id: The ID of the target Discord server (guild).
    """
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return '{"error": "Guild not found."}'
    return await list_category(guild)