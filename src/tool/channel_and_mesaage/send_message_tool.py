from bot import bot
from calling_funciton.channel_and_mesaage.send_message import send_message

async def send_message_tool(channel_id: str, content: str) -> str:
    """Send a text message to a specific Discord channel.
    
    Args:
        channel_id: The ID of the destination Discord channel.
        content: The text content of the message to send.
    """
    channel = bot.get_channel(int(channel_id))
    return await send_message(channel, content)