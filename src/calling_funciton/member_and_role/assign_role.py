import discord

async def assign_role(
    guild: discord.Guild,
    user_id: str | int,
    role_id: str | int,
) -> str:
    """Assign an existing role to a server member by user_id and role_id."""
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

    if role in member.roles:
        return f"Notice: Member '{member.display_name}' already has '{role.name}'."

    try:
        await member.add_roles(role)
        return f"Successfully added role '{role.name}' to '{member.display_name}'."
    except discord.Forbidden:
        return "Error: Missing permissions or role is higher than bot's role."
    except Exception as e:
        return f"Error: {str(e)}"
