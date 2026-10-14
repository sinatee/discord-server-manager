from client_state import get_bot
from calling_funciton.server_info.list_channel import list_channel

async def list_channel_tool(guild_id: str) -> str:
    """List all channels in a Discord server.

    Args:
        guild_id: The ID of the target Discord server (guild).
    """
    bot = get_bot()
    if not bot:
        return '{"error": "Bot not initialized."}'

    guild = bot.get_guild(int(guild_id))
    if not guild:
        return '{"error": "Guild not found."}'
    return await list_channel(guild)