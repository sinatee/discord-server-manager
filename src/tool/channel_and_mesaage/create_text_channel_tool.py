from client_state import get_bot
from calling_funciton.channel_and_mesaage.create_text_channel import create_text_channel

async def create_text_channel_tool(guild_id: str, name: str, category_id: str | None = None) -> str:
    """Create a new text channel in a Discord server, optionally inside a category.

    Args:
        guild_id: The ID of the target Discord server (guild).
        name: The name of the new text channel.
        category_id: The ID of the category channel to place it under (optional).
    """
    bot = get_bot()
    if not bot:
        return "Error: Bot not initialized."

    guild = bot.get_guild(int(guild_id))
    if not guild:
        return "Error: Guild not found."

    return await create_text_channel(guild, name, category_id)