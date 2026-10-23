from client_state import get_bot
from calling_funciton.member_and_role.create_role import create_role

async def create_role_tool(
    guild_id: str,
    name: str,
    color_hex: str | None = None,
    hoist: bool = False,
    preset: str = "default",
) -> str:
    """Create a new role in a Discord server with optional color, hoist, and permission preset.
    
    Args:
        guild_id: The ID of the target Discord server (guild).
        name: The name of the new role.
        color_hex: Optional hex color code (e.g. #FF0000).
        hoist: Whether to display members separately in the sidebar.
        preset: Permission preset name (e.g. admin, moderator, read_only, default).
    """
    guild = get_bot().get_guild(int(guild_id))
    if not guild:
        return "Error: Guild not found."
    return await create_role(guild, name, color_hex, hoist, preset)