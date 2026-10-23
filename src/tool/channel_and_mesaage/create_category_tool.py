from client_state import get_bot
from calling_funciton.channel_and_mesaage.create_category import create_category

async def create_category_tool(guild_id: str, name: str) -> str:
    """Create a new category in a Discord server.
    
    Args:
        guild_id: The ID of the target Discord server (guild).
        name: The name of the category (1 to 100 characters).
    """
    guild = get_bot().get_guild(int(guild_id))
    if not guild:
        return "Error: Guild not found."
    return await create_category(guild, name)