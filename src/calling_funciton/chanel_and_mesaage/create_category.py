import discord


async def create_category(guild: discord.Guild, name: str) -> str:
    """Create a category and return its name and ID."""
    if guild is None:
        return "Error: Guild not found."
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        return "Error: Category name must contain 1–100 characters."
    try:
        category = await guild.create_category(name.strip())
        return f"Created category '{category.name}' (ID: {category.id})."
    except discord.Forbidden:
        return "Error: Bot needs Manage Channels permission."
    except discord.HTTPException as error:
        return f"Error creating category: {error}"
