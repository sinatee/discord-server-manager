import discord


async def move_category(
    guild: discord.Guild, category_id: str | int, position: int
) -> str:
    """Reorder a category by its Discord position; do not move child channels."""
    if guild is None:
        return "Error: Guild not found."
    try:
        category_id = int(category_id)
    except (ValueError, TypeError):
        return "Error: category_id must be a number."
    if isinstance(position, bool) or not isinstance(position, int) or position < 0:
        return "Error: position must be a non-negative integer."
    category = guild.get_channel(category_id)
    if not isinstance(category, discord.CategoryChannel):
        return "Error: Category not found in this server."
    try:
        await category.edit(position=position)
        return f"Requested category '{category.name}' move to position {position}."
    except discord.Forbidden:
        return "Error: Bot needs Manage Channels permission."
    except discord.NotFound:
        return "Error: Category no longer exists."
    except discord.HTTPException as error:
        return f"Error moving category: {error}"
