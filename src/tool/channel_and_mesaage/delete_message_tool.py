import discord
from client_state import get_bot
from calling_funciton.channel_and_mesaage.delete_message import delete_message

async def delete_message_tool(channel_id: str, message_id: str) -> str:
    """Fetch and delete a specific message from a Discord channel.
    
    Args:
        channel_id: The ID of the Discord channel.
        message_id: The ID of the message to delete.
    """
    channel = get_bot().get_channel(int(channel_id))
    if not isinstance(channel, discord.TextChannel):
        return "Error: Text channel not found."
    return await delete_message(channel, message_id)