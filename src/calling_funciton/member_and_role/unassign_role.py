import discord

async def unassign_role(
    guild: discord.Guild,
    user_id: str | int,
    role_id: str | int,
) -> str:
    """Remove an existing role from a server member by user_id and role_id."""
    if not guild:
        return "Error: Guild not found."

    try:
        u_id = int(user_id)
        r_id = int(role_id)
    except (ValueError, TypeError):
        return "Error: user_id and role_id must be valid numbers."

    member = guild.get_member(u_id)
    if not member:
        try:
            member = await guild.fetch_member(u_id)
        except Exception:
            return f"Error: Member '{u_id}' not found."

    role = guild.get_role(r_id)
    if not role:
        return f"Error: Role '{r_id}' not found."

    if role not in member.roles:
        return f"Notice: Member '{member.display_name}' does not have '{role.name}'."

    bot_member = guild.me
    if role >= bot_member.top_role:
        return (
            f"Error: Cannot remove role '{role.name}' because it is higher than "
            f"or equal to the bot's highest role ('{bot_member.top_role.name}')."
        )

    try:
        await member.remove_roles(role)
        return f"Successfully removed role '{role.name}' from '{member.display_name}'."
    except discord.Forbidden:
        return "Error: Missing permissions or role is higher than bot's role."
    except Exception as e:
        return f"Error: {str(e)}"