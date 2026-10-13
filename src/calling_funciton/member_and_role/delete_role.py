import discord

async def delete_role(
    guild: discord.Guild,
    role_id: str | int,
) -> str:
    """Delete an existing role from the server by role_id."""
    if not guild:
        return "Error: Guild not found."

    try:
        r_id = int(role_id)
    except (ValueError, TypeError):
        return "Error: role_id must be a valid number."

    role = guild.get_role(r_id)
    if not role:
        return f"Error: Role with ID '{r_id}' not found."

    if role.is_default():
        return "Error: Cannot delete the default '@everyone' role."

    if role.is_bot_managed() or role.is_integration():
        return f"Error: Cannot delete '{role.name}' because it is managed by an integration/bot."

    bot_member = guild.me
    if role >= bot_member.top_role:
        return (
            f"Error: Cannot delete role '{role.name}' because it is higher than "
            f"or equal to the bot's highest role ('{bot_member.top_role.name}')."
        )

    role_name = role.name
    try:
        await role.delete()
        return f"Successfully deleted role '{role_name}' (ID: {r_id})."
    except discord.Forbidden:
        return f"Error: Missing permissions to delete role '{role_name}'."
    except Exception as e:
        return f"Error deleting role: {str(e)}"