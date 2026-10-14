import json

import discord


async def list_channel(guild: discord.Guild) -> str:
    """List all channels in the specified server as JSON."""
    if guild is None:
        return json.dumps({"error": "Guild not found."})

    channels_data = []
    for channel in guild.channels:
        channels_data.append({
            "id": str(channel.id),
            "name": channel.name,
            "type": str(channel.type),
            "position": channel.position,
        })

    return json.dumps(channels_data, ensure_ascii=False, indent=2)
