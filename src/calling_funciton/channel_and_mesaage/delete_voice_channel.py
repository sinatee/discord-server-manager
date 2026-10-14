import discord


async def delete_voice_channel(guild: discord.Guild, channel_id: str | int) -> str:
    """Delete a voice channel from the specified server."""
    if guild is None:
        return "Error: Guild not found."

    try:
        channel_id = int(channel_id)
    except (ValueError, TypeError):
        return "Error: channel_id must be a number."

    channel = guild.get_channel(channel_id)
    if not isinstance(channel, discord.VoiceChannel):
        return "Error: Voice channel not found in this server."

    channel_name = channel.name
    try:
        await channel.delete()
        return f"Deleted voice channel '{channel_name}' (ID: {channel_id})."
    except discord.Forbidden:
        return "Error: Bot needs Manage Channels permission."
    except discord.NotFound:
        return "Error: Voice channel was already deleted."
    except discord.HTTPException as error:
        return f"Error deleting voice channel: {error}"
