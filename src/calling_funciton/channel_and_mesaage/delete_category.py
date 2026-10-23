import discord


async def delete_category(guild: discord.Guild, category_id: str | int) -> str:
    """Delete a category only; its child channels are not deleted."""
    if guild is None:
        return "Error: Guild not found."
    try:
        category_id = int(category_id)
    except (ValueError, TypeError):
        return "Error: category_id must be a number."
    category = guild.get_channel(category_id)
    if not isinstance(category, discord.CategoryChannel):
        return "Error: Category not found in this server."
    name = category.name
    try:
        await category.delete()
        return f"Deleted category '{name}' (ID: {category_id}); child channels remain."
    except discord.Forbidden:
        return "Error: Bot needs Manage Channels permission."
    except discord.NotFound:
        return "Error: Category was already deleted."
    except discord.HTTPException as error:
        return f"Error deleting category: {error}"
