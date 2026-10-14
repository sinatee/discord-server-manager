import discord


async def create_text_channel(
    guild: discord.Guild,
    name: str,
    category_id: str | int | None = None,
) -> str:
    """Create a text channel, optionally inside a category."""
    if guild is None:
        return "Error: Guild not found."
    if not isinstance(name, str) or not name.strip():
        return "Error: Channel name cannot be empty."

    category = None
    if category_id is not None:
        try:
            category_id = int(category_id)
        except (ValueError, TypeError):
            return "Error: category_id must be a number."

        category = guild.get_channel(category_id)
        if not isinstance(category, discord.CategoryChannel):
            return "Error: Category not found in this server."

    try:
        channel = await guild.create_text_channel(name.strip(), category=category)
        return f"Created text channel '{channel.name}' (ID: {channel.id})."
    except discord.Forbidden:
        return "Error: Bot needs Manage Channels permission."
    except discord.HTTPException as error:
        return f"Error creating text channel: {error}"
