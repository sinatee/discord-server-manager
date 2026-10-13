from bot import bot
from calling_funciton.channel_and_mesaage.delete_category import delete_category

async def delete_category_tool(guild_id: str, category_id: str) -> str:
    """Delete a category from a Discord server without deleting its child channels.
    
    Args:
        guild_id: The ID of the target Discord server (guild).
        category_id: The ID of the category to delete.
    """
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return "Error: Guild not found."
    return await delete_category(guild, category_id)