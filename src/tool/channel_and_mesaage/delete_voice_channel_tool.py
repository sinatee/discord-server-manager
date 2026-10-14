from client_state import get_bot
from calling_funciton.channel_and_mesaage.delete_voice_channel import delete_voice_channel

async def delete_voice_channel_tool(guild_id: str, channel_id: str) -> str:
    """Delete a voice channel from the specified Discord server.

    Args:
        guild_id: The ID of the target Discord server (guild).
        channel_id: The ID of the voice channel to delete.
    """
    bot = get_bot()
    if not bot:
        return "Error: Bot not initialized."

    guild = bot.get_guild(int(guild_id))
    if not guild:
        return "Error: Guild not found."

    return await delete_voice_channel(guild, channel_id)