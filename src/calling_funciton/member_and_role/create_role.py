import discord

PRESET_PERMISSIONS = {
    "admin": discord.Permissions(administrator=True),
    "moderator": discord.Permissions(
        view_channel=True,
        send_messages=True,
        manage_messages=True,
        kick_members=True,
        ban_members=True,
        mute_members=True,
    ),
    "read_only": discord.Permissions(
        view_channel=True,
        read_message_history=True,
    ),
}

async def create_role(
    guild: discord.Guild,
    name: str,
    color_hex: str | None = None,
    hoist: bool = False,
    preset: str = "default",
) -> str:
    """Create a new role with optional color, hoist (sidebar group), and permission preset."""
    if not guild:
        return "Error: Guild not found."

    clean_name = name.strip() if name else ""
    if not clean_name:
        return "Error: Role name cannot be empty."

    color = discord.Color.default()
    if color_hex:
        try:
            color = discord.Color(int(color_hex.lstrip("#"), 16))
        except ValueError:
            return f"Error: Invalid hex color '{color_hex}'."

    perms = PRESET_PERMISSIONS.get(preset.lower().strip(), discord.Permissions.none())

    try:
        role = await guild.create_role(
            name=clean_name,
            color=color,
            hoist=hoist,
            mentionable=False,
            permissions=perms,
            reason=f"Role created with {preset} preset",
        )
        return f"Successfully created role '{role.name}' (ID: {role.id}, Hoist: {hoist})."

    except discord.Forbidden:
        return "Error: Bot lacks 'Manage Roles' permission or hierarchy issue."
    except Exception as e:
        return f"Error: {str(e)}"