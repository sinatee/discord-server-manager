from client_state import get_bot
from calling_funciton.server_info.get_message_history import get_message_history

async def get_message_history_tool(guild_id: str, channel_id: str, limit: int = 10) -> str:
    """Get recent message history from a text channel to read or find message IDs to delete.

    Args:
        guild_id: The ID of the target Discord server (guild).
        channel_id: The ID of the text channel.
        limit: Number of recent messages to fetch (default: 10, max: 50).
    """
    bot = get_bot()
    if not bot:
        return '{"error": "Bot not initialized."}'

    guild = bot.get_guild(int(guild_id))
    if not guild:
        return '{"error": "Guild not found."}'

    return await get_message_history(guild, channel_id, limit)