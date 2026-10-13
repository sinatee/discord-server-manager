from bot import bot
from calling_funciton.channel_and_mesaage.move_category import move_category

async def move_category_tool(guild_id: str, category_id: str, position: int) -> str:
    """Reorder a category in a Discord server by its position.
    
    Args:
        guild_id: The ID of the target Discord server (guild).
        category_id: The ID of the category to move.
        position: The new non-negative integer position for the category.
    """
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return "Error: Guild not found."
    return await move_category(guild, category_id, position)