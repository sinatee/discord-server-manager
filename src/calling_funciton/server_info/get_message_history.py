import json
import discord

async def get_message_history(guild: discord.Guild, channel_id: str | int, limit: int = 10) -> str:
    """Fetch the latest messages from a text channel formatted as JSON."""
    if not guild:
        return json.dumps({"error": "Guild not found."})

    try:
        channel_id = int(channel_id)
    except (ValueError, TypeError):
        return json.dumps({"error": "channel_id must be a valid number."})

    channel = guild.get_channel(channel_id)
    if not channel or not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": "Text channel not found in this server."})

    # Keep limit reasonable so LLM context isn't overloaded
    try:
        limit = max(1, min(int(limit), 50))
    except (ValueError, TypeError):
        limit = 10

    messages_data = []
    try:
        async for msg in channel.history(limit=limit):
            messages_data.append({
                "message_id": str(msg.id),
                "author": msg.author.display_name,
                "author_id": str(msg.author.id),
                "is_bot": msg.author.bot,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            })
    except discord.Forbidden:
        return json.dumps({"error": "Bot lacks Read Message History permission."})
    except discord.HTTPException as error:
        return json.dumps({"error": f"Error fetching history: {error}"})

    return json.dumps(messages_data, ensure_ascii=False, indent=2)