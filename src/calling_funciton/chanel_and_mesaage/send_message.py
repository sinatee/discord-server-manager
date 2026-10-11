import discord

async def send_message(channel: discord.TextChannel, content: str) -> str:
    """send message to selected chanel"""
    if channel is None:
        return "Error: Channel not found (chanel is None)"
    if not content or not content.strip():
        return "Error: Message content cannot be empty."

    try:
        chunk_size = 2000
        sent_count = 0

        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            await channel.send(chunk)
            sent_count += 1
        return f"Successfully sent message to #{channel.name} ({sent_count} message(s) delivered)."

    except discord.Forbidden:
        return f"Error: Missing permissions to send messages in #{channel.name}."
    except Exception as e:
        return f"Error: Failed to send message: {str(e)}"