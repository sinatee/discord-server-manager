import inspect
import json
import re
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone

import discord
import ollama

from client_state import get_bot
from tool.channel_and_mesaage.send_message_tool import send_message_tool
from tool.channel_and_mesaage.delete_message_tool import delete_message_tool
from tool.server_info.list_category_tool import list_category_tool
from tool.channel_and_mesaage.move_category_tool import move_category_tool
from tool.channel_and_mesaage.create_category_tool import create_category_tool
from tool.channel_and_mesaage.delete_category_tool import delete_category_tool
from tool.server_info.list_member_tool import list_member_tool
from tool.server_info.list_roles_tool import list_roles_tool
from tool.member_and_role.assign_role_tool import assign_role_tool
from tool.member_and_role.unassign_role_tool import unassign_role_tool
from tool.member_and_role.create_role_tool import create_role_tool
from tool.member_and_role.delete_role_tool import delete_role_tool
from tool.server_info.list_channel_tool import list_channel_tool
from tool.channel_and_mesaage.create_text_channel_tool import create_text_channel_tool
from tool.channel_and_mesaage.delete_text_channel_tool import delete_text_channel_tool
from tool.channel_and_mesaage.create_voice_channel_tool import create_voice_channel_tool
from tool.channel_and_mesaage.delete_voice_channel_tool import delete_voice_channel_tool
from tool.server_info.get_message_history_tool import get_message_history_tool


TOOLS = [
    send_message_tool,
    delete_message_tool,
    list_category_tool,
    move_category_tool,
    create_category_tool,
    delete_category_tool,
    list_member_tool,
    list_roles_tool,
    assign_role_tool,
    unassign_role_tool,
    create_role_tool,
    delete_role_tool,
    list_channel_tool,
    create_text_channel_tool,
    delete_text_channel_tool,
    create_voice_channel_tool,
    delete_voice_channel_tool,
    get_message_history_tool,
]
AVAILABLE_TOOLS = {t.__name__: t for t in TOOLS}
TOOL_ARGUMENT_CONTRACTS = {
    "send_message_tool": {"channel_id", "content"},
    "delete_message_tool": {"channel_id", "message_id"},
    "get_message_history_tool": {"guild_id", "channel_id", "limit"},
    "list_category_tool": {"guild_id"},
    "create_category_tool": {"guild_id", "name"},
    "delete_category_tool": {"guild_id", "category_id"},
    "move_category_tool": {"guild_id", "category_id", "position"},
    "list_channel_tool": {"guild_id"},
    "create_text_channel_tool": {"guild_id", "name", "category_id"},
    "delete_text_channel_tool": {"guild_id", "channel_id"},
    "create_voice_channel_tool": {"guild_id", "name", "category_id"},
    "delete_voice_channel_tool": {"guild_id", "channel_id"},
    "list_member_tool": {"guild_id"},
    "list_roles_tool": {"guild_id"},
    "create_role_tool": {"guild_id", "name", "color_hex", "hoist", "preset"},
    "assign_role_tool": {"guild_id", "user_id", "role_id"},
    "unassign_role_tool": {"guild_id", "user_id", "role_id"},
    "delete_role_tool": {"guild_id", "role_id"},
}
DELETE_TOOLS = {
    "delete_message_tool",
    "delete_category_tool",
    "delete_text_channel_tool",
    "delete_voice_channel_tool",
    "delete_role_tool",
}
CONFIRMATION_TIMEOUT = timedelta(minutes=5)
DISCORD_MESSAGE_LIMIT = 2000
request_context = ContextVar("request_context", default=None)
pending_deletions = {}


def set_request_context(
    guild_id: int,
    user_id: int,
    channel_id: int,
):
    """Store the Discord request identity for the current agent execution."""
    return request_context.set((guild_id, user_id, channel_id))


def reset_request_context(token) -> None:
    request_context.reset(token)


def format_deletion_confirmation(heading: str, previews: list[str]) -> str:
    """Keep a confirmation preview below Discord's 2,000-character limit."""
    suffix = "\nReply `confirm` or `ยืนยัน` within 5 minutes to continue."
    message = f"{heading}\n"
    for index, preview in enumerate(previews):
        # A channel/message name can be unusually long, so cap each preview too.
        preview = preview[:300]
        candidate = f"{message}{preview}\n"
        if len(candidate) + len(suffix) <= DISCORD_MESSAGE_LIMIT:
            message = candidate
            continue

        remaining = len(previews) - index
        omitted = f"... and {remaining} more item(s) from verified history.\n"
        if len(message) + len(omitted) + len(suffix) <= DISCORD_MESSAGE_LIMIT:
            message += omitted
        break
    return f"{message.rstrip()}{suffix}"


async def confirm_pending_deletion(guild_id: int, user_id: int, channel_id: int) -> str:
    """Execute the pending deletion batch for the same user and channel."""
    key = (guild_id, user_id, channel_id)
    pending = pending_deletions.pop(key, None)
    if pending is None:
        return "There is no pending deletion to confirm."

    deletions, expires_at = pending
    if datetime.now(timezone.utc) > expires_at:
        return "The deletion confirmation expired. Please make the request again."

    results = []
    for tool_name, arguments, _preview in deletions:
        results.append(await execute_tool(tool_name, arguments, confirmed=True))
    return "\n".join(results)


def cancel_pending_deletion(guild_id: int, user_id: int, channel_id: int) -> str:
    """Discard an unconfirmed deletion batch for the same user and channel."""
    key = (guild_id, user_id, channel_id)
    pending = pending_deletions.pop(key, None)
    if pending is None:
        return "There is no pending deletion to cancel."
    return "Deletion cancelled. No messages or server items were deleted."


async def get_deletion_preview(tool_name: str, arguments: dict) -> str:
    """Return a human-readable target preview without mutating Discord state."""
    bot = get_bot()
    if bot is None:
        return "Error: Bot not initialized."

    if tool_name == "delete_message_tool":
        channel = bot.get_channel(int(arguments["channel_id"]))
        if not isinstance(channel, discord.TextChannel):
            return "Error: Text channel not found."

        try:
            message = await channel.fetch_message(int(arguments["message_id"]))
        except discord.NotFound:
            return "Error: Message not found in this channel."
        except discord.Forbidden:
            return "Error: Bot lacks permission to read this message."
        except discord.HTTPException as error:
            return f"Error: Unable to read message: {error}"

        content = message.content.replace("\n", " ").strip()
        preview = content[:80] + ("..." if len(content) > 80 else "")
        return (
            f"- Message from {message.author.display_name} in #{channel.name}: "
            f"{preview or '[no text]'} (ID: {message.id})"
        )

    guild = bot.get_guild(int(arguments["guild_id"]))
    if guild is None:
        return "Error: Guild not found."

    if tool_name in {"delete_text_channel_tool", "delete_voice_channel_tool"}:
        channel = guild.get_channel(int(arguments["channel_id"]))
        expected_type = discord.TextChannel if tool_name == "delete_text_channel_tool" else discord.VoiceChannel
        if not isinstance(channel, expected_type):
            return "Error: Requested channel type was not found in this server."
        channel_type = "Text" if tool_name == "delete_text_channel_tool" else "Voice"
        return f"- {channel_type} channel: #{channel.name} (ID: {channel.id})"

    if tool_name == "delete_category_tool":
        category = guild.get_channel(int(arguments["category_id"]))
        if not isinstance(category, discord.CategoryChannel):
            return "Error: Category not found in this server."
        return f"- Category: {category.name} (ID: {category.id})"

    if tool_name == "delete_role_tool":
        role = guild.get_role(int(arguments["role_id"]))
        if role is None:
            return "Error: Role not found in this server."
        return f"- Role: {role.name} (ID: {role.id})"

    return "Error: Unsupported delete tool."

async def execute_tool(tool_name: str, arguments: dict, *, confirmed: bool = False) -> str:
    """Dynamically execute a tool function by name with given arguments."""

    arguments = dict(arguments or {})
    print(f"[tool call] {tool_name} {arguments}")

    if tool_name not in AVAILABLE_TOOLS:
        return f"Error: Tool '{tool_name}' not found."

    contract_arguments = TOOL_ARGUMENT_CONTRACTS[tool_name]
    unsupported_contract_arguments = set(arguments) - contract_arguments
    if unsupported_contract_arguments:
        print(
            f"[tool contract] Ignoring unsupported arguments for {tool_name}: "
            f"{sorted(unsupported_contract_arguments)}"
        )
        arguments = {
            name: value for name, value in arguments.items()
            if name in contract_arguments
        }

    tool_func = AVAILABLE_TOOLS[tool_name]
    parameters = inspect.signature(tool_func).parameters
    accepted_arguments = {
        name
        for name, parameter in parameters.items()
        if parameter.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    }
    ignored_arguments = set(arguments) - accepted_arguments
    if ignored_arguments:
        print(
            f"[tool validation] Ignoring unsupported arguments for {tool_name}: "
            f"{sorted(ignored_arguments)}"
        )
        arguments = {
            name: value for name, value in arguments.items()
            if name in accepted_arguments
        }

    missing_arguments = [
        name
        for name, parameter in parameters.items()
        if parameter.default is inspect.Parameter.empty
        and parameter.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
        and name not in arguments
    ]
    if missing_arguments:
        return (
            f"Error: Tool '{tool_name}' is missing required arguments: "
            f"{', '.join(missing_arguments)}."
        )

    if tool_name in DELETE_TOOLS and not confirmed:
        context = request_context.get()
        if context is None:
            return "Error: Delete commands require a Discord request context."

        guild_id, user_id, source_channel_id = context
        preview = await get_deletion_preview(tool_name, arguments)
        if preview.startswith("Error:"):
            return preview

        key = (guild_id, user_id, source_channel_id)
        pending = pending_deletions.get(key)
        if pending is None or datetime.now(timezone.utc) > pending[1]:
            pending = ([], datetime.now(timezone.utc) + CONFIRMATION_TIMEOUT)
            pending_deletions[key] = pending

        deletions, _expires_at = pending
        deletion = (tool_name, arguments, preview)
        if deletion not in deletions:
            deletions.append(deletion)
        return "Confirmation required."

    try:
        return await tool_func(**arguments)
    except Exception as e:
        return f"Error executing tool {tool_name}: {str(e)}"

SYSTEM_PROMPT = """
You are a Discord server management bot. Reply in the user's language; be concise and truthful.

CONTEXT
- Use guild_id for server actions and the current channel_id for "this channel" actions.
- Mentioned users include their IDs. Never invent IDs.
- The application sends normal replies. Use send_message_tool only when the user explicitly asks
  to send a message to a channel.

TOOLS
- Follow each tool's signature exactly. Never add arguments from context unless that tool needs them.
- Text/voice creation: create_text_channel_tool or create_voice_channel_tool(guild_id, name,
  optional category_id). Text/voice deletion: matching delete tool(guild_id, channel_id).
- List channels/categories/members/roles with their matching list tool. Use matching tools for
  category, role, and message actions. Use get_message_history_tool(guild_id, channel_id, limit)
  before deleting messages.
- send_message_tool accepts only channel_id and content. Do not pass channel_id to create tools.

BEHAVIOR
- For a category name, list categories, require exactly one match, then use its ID. Otherwise ask.
- For a channel name, list channels and require an exact name and requested type match. Otherwise ask.
- For actions, call tools; never claim success without a successful tool result.
- For dependent multi-step work, continue calling tools until every requested step is complete.
  Use IDs returned by a prior tool (for example a newly-created category ID), never invent them.
- For lists, return clean bullet names, not raw JSON. Show IDs only when requested or needed.
- If information is missing or a tool errors, ask one clear question or report the error.

DELETION
- Never delete immediately: the application shows a preview and requires confirm.
- For multiple independent requests, call all matching tools in order; deletion tools form one batch.
- For messages from a mentioned user in this channel: use context IDs, get up to 50 recent messages,
  select only matching author_id values, then call delete_message_tool for each selected message.
- If no target user is mentioned, ask the user to mention them.
"""

LOOP_LIMIT = 10
MUTATING_TOOLS = {
    "send_message_tool",
    "delete_message_tool",
    "create_category_tool",
    "delete_category_tool",
    "move_category_tool",
    "create_text_channel_tool",
    "delete_text_channel_tool",
    "create_voice_channel_tool",
    "delete_voice_channel_tool",
    "create_role_tool",
    "assign_role_tool",
    "unassign_role_tool",
    "delete_role_tool",
}
CREATION_TOOLS = {
    "create_category_tool",
    "create_text_channel_tool",
    "create_voice_channel_tool",
    "create_role_tool",
}
client = ollama.AsyncClient()


def is_delete_all_messages_request(user_text: str) -> bool:
    """Identify explicit requests to delete every recent message in the current channel."""
    normalized_text = get_user_command(user_text).lower()
    english_request = bool(re.search(
        r"\b(?:delete|remove)\s+(?:all|every)\s+messages?\b",
        normalized_text,
    ))
    thai_request = bool(re.search(
        r"ลบ\s*(?:ทุก\s*)?ข้อความ\s*(?:ทั้งหมด|ทุก)?\s*(?:นี้)?"
        r"\s*(?:ใน\s*)?(?:ช่อง|แชนแนล|channel)\s*(?:นี้)?",
        normalized_text,
    )) or "ลบทุกข้อความ" in normalized_text
    return english_request or thai_request


def is_delete_bot_messages_request(user_text: str) -> bool:
    """Identify a request to delete only bot-authored messages."""
    command = get_user_command(user_text).lower()
    return bool(re.search(
        r"\b(?:delete|remove)\s+(?:all\s+)?messages?\s+"
        r"(?:sent\s+)?by\s+(?:the\s+)?bots?\b",
        command,
    )) or "ลบข้อความของบอท" in command


def get_requested_history_limit(user_text: str, default: int = 50) -> int:
    """Use an explicit 'last N messages' limit while keeping Discord reads bounded."""
    command = get_user_command(user_text).lower()
    match = re.search(r"\b(?:last|latest)\s+(\d+)\s+messages?\b", command)
    if match is None:
        return default
    return max(1, min(int(match.group(1)), 50))


def get_post_target_channel_name(user_text: str) -> str | None:
    """Read the channel name from 'post ... inside the <name> channel'."""
    command = get_user_command(user_text)
    match = re.search(
        r"\b(?:post|send)\s+[\"“].+?[\"”]\s+(?:inside|in)\s+"
        r"(?:the\s+)?([\w-]+)\s+channel\b",
        command,
        re.IGNORECASE,
    )
    return match.group(1) if match else None


def get_user_command(user_text: str) -> str:
    """Extract the command from the context block supplied by bot.py."""
    match = re.search(r"^User Message:\s*(.+)$", user_text, re.MULTILINE)
    return match.group(1) if match else user_text


def get_single_message_id_request(user_text: str) -> str | None:
    """Find an explicit Discord message ID in a delete-one-message command."""
    command = get_user_command(user_text)
    patterns = (
        r"\b(?:delete|remove)\s+(?:the\s+)?(?:message|msg)\s*"
        r"(?:id\s*)?[:#]?\s*(\d{15,22})\b",
        r"ลบ\s*ข้อความ\s*(?:id\s*)?[:#]?\s*(\d{15,22})\b",
    )
    for pattern in patterns:
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def is_delete_mentioned_user_messages_request(user_text: str) -> bool:
    """Identify a request to delete messages authored by a mentioned user."""
    command = get_user_command(user_text).lower()
    return bool(re.search(
        r"\b(?:delete|remove)\s+(?:all\s+)?messages?\s+(?:from|of)\b",
        command,
    )) or bool(re.search(r"ลบ\s*ข้อความ\s*(?:ทั้งหมด\s*)?ของ", command))


def get_mentioned_user_ids(user_text: str) -> set[str]:
    """Read the verified mention IDs inserted by bot.py into the context block."""
    match = re.search(r"^Mentioned users:\s*(.+)$", user_text, re.MULTILINE)
    if match is None or match.group(1).strip() == "None":
        return set()
    return set(re.findall(r"\(ID:\s*(\d+)\)", match.group(1)))


async def get_current_channel_history(limit: int = 50) -> list[dict] | str:
    """Fetch recent history using only the guild and channel in Discord context."""
    context = request_context.get()
    if context is None:
        return "Error: Delete commands require a Discord request context."

    guild_id, _user_id, channel_id = context
    history_result = await execute_tool("get_message_history_tool", {
        "guild_id": str(guild_id),
        "channel_id": str(channel_id),
        "limit": limit,
    })
    try:
        history = json.loads(history_result)
    except json.JSONDecodeError:
        return "Error: Unable to read message history."
    return history if isinstance(history, list) else str(history_result)


def get_delete_text_channel_name_request(user_text: str) -> str | None:
    """Read a quoted text-channel name from an explicit delete request."""
    command = get_user_command(user_text).strip()
    patterns = (
        # Accept the common misspelling "channal" too.
        r"\b(?:delete|remove)\s+text\s+chann(?:el|al)\s+name\s*"
        r"[\"“]([^\"”]+)[\"”]",
        r"\b(?:delete|remove)\s+(?:the\s+)?(?:text\s+)?chann(?:el|al)\s+"
        r"(?:named|name)\s*[\"“]([^\"”]+)[\"”]",
        r"ลบ\s*(?:ช่อง\s*ข้อความ|text\s*channel)\s*(?:ชื่อ)?\s*"
        r"[\"“]([^\"”]+)[\"”]",
    )
    for pattern in patterns:
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


async def queue_named_text_channel_deletion(channel_name: str) -> str:
    """Resolve a text channel by exact Discord name, then queue it for deletion."""
    context = request_context.get()
    if context is None:
        return "Error: Delete commands require a Discord request context."

    guild_id, _user_id, _source_channel_id = context
    channels_result = await execute_tool("list_channel_tool", {"guild_id": str(guild_id)})
    try:
        channels = json.loads(channels_result)
    except json.JSONDecodeError:
        return "Error: Unable to read the server channel list."
    if not isinstance(channels, list):
        return str(channels_result)

    matches = [
        channel for channel in channels
        if channel.get("type") == "text" and channel.get("name") == channel_name
    ]
    if not matches:
        return f"No text channel named '{channel_name}' was found. Nothing was deleted."
    if len(matches) > 1:
        ids = ", ".join(str(channel["id"]) for channel in matches)
        return (
            f"More than one text channel is named '{channel_name}' (IDs: {ids}). "
            "Please delete by a specific channel ID."
        )

    result = await execute_tool("delete_text_channel_tool", {
        "guild_id": str(guild_id),
        "channel_id": str(matches[0]["id"]),
    })
    if not str(result).startswith("Confirmation required."):
        return str(result)

    deletion = pending_deletions[context][0][-1]
    return format_deletion_confirmation(
        "The following text channel will be deleted:", [deletion[2]],
    )


async def queue_single_message_deletion(message_id: str) -> str:
    """Verify a user-provided ID against current-channel history and queue it."""
    context = request_context.get()
    if context is None:
        return "Error: Delete commands require a Discord request context."

    _guild_id, _user_id, channel_id = context
    history = await get_current_channel_history()
    if isinstance(history, str):
        return history

    valid_ids = {
        str(message["message_id"])
        for message in history if message.get("message_id")
    }
    if message_id not in valid_ids:
        return (
            "That message ID was not found among the latest 50 messages in this channel. "
            "Use an ID returned by this channel's message history."
        )

    result = await execute_tool("delete_message_tool", {
        "channel_id": str(channel_id),
        "message_id": message_id,
    })
    if not str(result).startswith("Confirmation required."):
        return str(result)

    deletion = pending_deletions[context][0][-1]
    return format_deletion_confirmation(
        "The following message will be deleted:", [deletion[2]],
    )


async def queue_mentioned_user_message_deletions(user_ids: set[str]) -> str:
    """Queue recent current-channel messages written by the mentioned user(s)."""
    context = request_context.get()
    if context is None:
        return "Error: Delete commands require a Discord request context."
    if not user_ids:
        return "Please mention the user whose messages you want to delete."

    _guild_id, _user_id, channel_id = context
    history = await get_current_channel_history()
    if isinstance(history, str):
        return history

    message_ids = [
        str(message["message_id"])
        for message in history
        if message.get("message_id") and str(message.get("author_id")) in user_ids
    ]
    if not message_ids:
        return "No recent messages from the mentioned user were found in this channel."

    queued = 0
    errors = []
    for message_id in message_ids:
        result = await execute_tool("delete_message_tool", {
            "channel_id": str(channel_id),
            "message_id": message_id,
        })
        if str(result).startswith("Confirmation required."):
            queued += 1
        else:
            errors.append(str(result))

    if not queued:
        return "\n".join(errors) or "No messages could be queued for deletion."

    previews = pending_deletions[context][0]
    confirmation = format_deletion_confirmation(
        f"The following {queued} message(s) from the mentioned user will be deleted:",
        [deletion[2] for deletion in previews],
    )
    return f"{confirmation}\n{' '.join(errors)}" if errors else confirmation


async def queue_all_recent_message_deletions() -> str:
    """Queue every recent message in the current channel from verified history."""
    context = request_context.get()
    if context is None:
        return "Error: Delete commands require a Discord request context."

    _guild_id, _user_id, channel_id = context
    history = await get_current_channel_history()
    if isinstance(history, str):
        return history

    message_ids = [
        str(message["message_id"])
        for message in history if message.get("message_id")
    ]
    if not message_ids:
        return "There are no recent messages in this channel to delete."

    queued = 0
    errors = []
    for message_id in message_ids:
        result = await execute_tool("delete_message_tool", {
            "channel_id": str(channel_id),
            "message_id": message_id,
        })
        if str(result).startswith("Confirmation required."):
            queued += 1
        else:
            errors.append(str(result))

    if not queued:
        return "\n".join(errors) or "No messages could be queued for deletion."

    previews = pending_deletions[context][0]
    confirmation = format_deletion_confirmation(
        f"The following {queued} recent message(s) will be deleted:",
        [deletion[2] for deletion in previews],
    )
    return f"{confirmation}\n{' '.join(errors)}" if errors else confirmation


async def queue_bot_message_deletions(limit: int) -> str:
    """Queue only bot-authored messages from the requested current-channel history."""
    context = request_context.get()
    if context is None:
        return "Error: Delete commands require a Discord request context."

    _guild_id, _user_id, channel_id = context
    history = await get_current_channel_history(limit)
    if isinstance(history, str):
        return history

    message_ids = [
        str(message["message_id"])
        for message in history
        if message.get("message_id") and message.get("is_bot") is True
    ]
    if not message_ids:
        return "No bot messages were found in the requested message history."

    queued = 0
    errors = []
    for message_id in message_ids:
        result = await execute_tool("delete_message_tool", {
            "channel_id": str(channel_id),
            "message_id": message_id,
        })
        if str(result).startswith("Confirmation required."):
            queued += 1
        else:
            errors.append(str(result))

    if not queued:
        return "\n".join(errors) or "No bot messages could be queued for deletion."

    previews = pending_deletions[context][0]
    confirmation = format_deletion_confirmation(
        f"The following {queued} bot message(s) will be deleted:",
        [deletion[2] for deletion in previews],
    )
    return f"{confirmation}\n{' '.join(errors)}" if errors else confirmation


async def run_agent(user_text: str) -> str | None:
    text_channel_name = get_delete_text_channel_name_request(user_text)
    if text_channel_name:
        context = request_context.get()
        if context is not None:
            pending_deletions.pop(context, None)
        return await queue_named_text_channel_deletion(text_channel_name)

    message_id = get_single_message_id_request(user_text)
    if message_id:
        context = request_context.get()
        if context is not None:
            # A new request must not reuse a previous, unconfirmed batch.
            pending_deletions.pop(context, None)
        return await queue_single_message_deletion(message_id)

    if is_delete_mentioned_user_messages_request(user_text):
        context = request_context.get()
        if context is not None:
            pending_deletions.pop(context, None)
        return await queue_mentioned_user_message_deletions(get_mentioned_user_ids(user_text))

    if is_delete_bot_messages_request(user_text):
        context = request_context.get()
        if context is not None:
            pending_deletions.pop(context, None)
        return await queue_bot_message_deletions(get_requested_history_limit(user_text))

    if is_delete_all_messages_request(user_text):
        context = request_context.get()
        if context is not None:
            pending_deletions.pop(context, None)
        return await queue_all_recent_message_deletions()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]
    nudged = False
    completed_action_results = []
    created_resources = {}
    created_category_ids = []
    created_text_channel_ids = {}
    post_target_channel_name = get_post_target_channel_name(user_text)
    command_depends_on_new_category = bool(re.search(
        r"\binside\s+it\b|ภายใน(?:หมวดหมู่)?นี้",
        get_user_command(user_text),
        re.IGNORECASE,
    ))
    for _ in range(LOOP_LIMIT):
        res = await client.chat(
            model="qwen3:1.7b",
            messages=messages,
            tools=TOOLS,
            keep_alive="10m",
            options={
                "temperature": 0,
                "num_ctx": 8192,
                "num_predict": 1500,
            },
        )
        if res.done_reason == "length":
            raise RuntimeError("Model reply was cut off (token limit reached).")
        
        messages.append(res.message)

        if not res.message.tool_calls:
            if completed_action_results:
                # Report the actual tool results, not a model-written summary.
                return "\n".join(completed_action_results)
            if res.message.content:
                return res.message.content

            if not nudged:
                nudged = True
                messages.append({
                    "role": "user",
                    "content": "Reply with a clear answer or call the required tool.",
                })
                continue

            raise RuntimeError("model never sent a message")

        confirmation_requested = False
        for call in res.message.tool_calls:
            name = call.function.name
            args = dict(call.function.arguments or {})

            if (
                command_depends_on_new_category
                and name in {"create_text_channel_tool", "create_voice_channel_tool"}
                and created_category_ids
                and str(args.get("category_id")) not in created_category_ids
            ):
                correct_category_id = created_category_ids[-1]
                print(
                    "[tool correction] Replacing model-provided category_id "
                    f"{args.get('category_id')} with newly-created category_id {correct_category_id}"
                )
                args["category_id"] = correct_category_id

            if (
                name == "send_message_tool"
                and post_target_channel_name is not None
                and post_target_channel_name.casefold() in created_text_channel_ids
                and str(args.get("channel_id"))
                != created_text_channel_ids[post_target_channel_name.casefold()]
            ):
                correct_channel_id = created_text_channel_ids[post_target_channel_name.casefold()]
                print(
                    "[tool correction] Replacing model-provided channel_id "
                    f"{args.get('channel_id')} with newly-created text channel_id {correct_channel_id}"
                )
                args["channel_id"] = correct_channel_id
            duplicate_creation = False
            resource_key = None
            if name in CREATION_TOOLS and args.get("guild_id") and args.get("name"):
                # Names, not model-provided container IDs, define duplicate
                # creation within one user request.  This blocks a model retry
                # from creating e.g. a second "reports" channel elsewhere.
                resource_key = (name, str(args["guild_id"]), str(args["name"]).casefold())
                if resource_key in created_resources:
                    duplicate_creation = True
                    result = (
                        "Duplicate creation ignored. The resource was already created in this request: "
                        f"{created_resources[resource_key]}"
                    )
                else:
                    result = await execute_tool(name, args)
            else:
                result = await execute_tool(name, args)

            if resource_key is not None and not duplicate_creation and not str(result).startswith("Error:"):
                created_resources[resource_key] = str(result)

            if name == "create_category_tool" and not str(result).startswith("Error:"):
                category_id_match = re.search(r"\(ID:\s*(\d+)\)", str(result))
                if category_id_match:
                    created_category_ids.append(category_id_match.group(1))

            if name == "create_text_channel_tool" and not str(result).startswith("Error:"):
                channel_id_match = re.search(r"\(ID:\s*(\d+)\)", str(result))
                channel_name = str(args.get("name", "")).casefold()
                if channel_id_match and channel_name:
                    created_text_channel_ids[channel_name] = channel_id_match.group(1)

            if str(result).startswith("Confirmation required."):
                confirmation_requested = True
                continue

            if name in MUTATING_TOOLS and not duplicate_creation:
                completed_action_results.append(str(result))

            # Give the model every result.  Dependent commands need the actual
            # ID returned by the preceding tool to continue safely.
            messages.append({
                "role": "tool",
                "content": str(result),
            })

        if confirmation_requested:
            context = request_context.get()
            pending_key = context if context else None
            deletions = pending_deletions[pending_key][0] if pending_key else []
            summary = "\n".join(completed_action_results)
            confirmation = format_deletion_confirmation(
                "The following will be deleted:",
                [deletion[2] for deletion in deletions],
            )
            return f"{summary}\n{confirmation}".strip()

    raise RuntimeError("Agent reached maximum execution step limit without finishing.")
