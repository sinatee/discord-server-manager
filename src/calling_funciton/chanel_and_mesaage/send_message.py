import discord

async def send_message(channel: discord.TextChannel, content: str) -> str:
    """send message to selected chanel"""
    if channel is None:
        return "Error: Channel not found (chanel is None)"
    
    message = await channel.send(content)
    return f"Sent message {message.id} to #{channel.name}."