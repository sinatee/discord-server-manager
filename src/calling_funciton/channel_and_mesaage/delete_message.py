import discord


async def delete_message(
    channel: discord.TextChannel, message_id: str | int
) -> str:
    """Fetch and delete one message from the specified channel."""
    if not isinstance(channel, discord.TextChannel):
        return "Error: Text channel not found."
    try:
        message_id = int(message_id)
    except (ValueError, TypeError):
        return "Error: message_id must be a number."
    try:
        message = await channel.fetch_message(message_id)
        await message.delete()
        return f"Deleted message {message_id} from #{channel.name}."
    except discord.NotFound:
        return "Error: Message or channel not found."
    except discord.Forbidden:
        return "Error: Check View Channel, Read Message History, and Manage Messages permissions."
    except discord.HTTPException as error:
        return f"Error deleting message: {error}"
