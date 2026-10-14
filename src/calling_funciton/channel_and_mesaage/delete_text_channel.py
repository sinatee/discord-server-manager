import discord


async def delete_text_channel(guild: discord.Guild, channel_id: str | int) -> str:
    """Delete a text channel from the specified server."""
    if guild is None:
        return "Error: Guild not found."

    try:
        channel_id = int(channel_id)
    except (ValueError, TypeError):
        return "Error: channel_id must be a number."

    channel = guild.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        return "Error: Text channel not found in this server."

    channel_name = channel.name
    try:
        await channel.delete()
        return f"Deleted text channel '{channel_name}' (ID: {channel_id})."
    except discord.Forbidden:
        return "Error: Bot needs Manage Channels permission."
    except discord.NotFound:
        return "Error: Text channel was already deleted."
    except discord.HTTPException as error:
        return f"Error deleting text channel: {error}"
