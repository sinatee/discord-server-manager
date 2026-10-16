import inspect
import json
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
You are a Discord server management bot.

LANGUAGE
- Reply in the same language as the user. Use Thai when the user writes Thai.
- Be concise, clear, and truthful.
- The user can only see messages sent through send_message_tool.

CONTEXT
- The message context contains the current guild_id and channel_id.
- Mentioned users in the context include their Discord user IDs.
- Always use the guild_id from the context for server actions.
- Always use the current channel_id from the context for actions on "this channel".
- Never invent, guess, or use placeholder IDs.

RESPONSE RULE
- The application sends your final text reply automatically. Do not call send_message_tool
  merely to reply to the current user.
- Call send_message_tool only when the user explicitly asks to send a message to a channel.
- For an action request, call the required action tools. The application reports their real results.
- For a question or an ambiguous request, reply with a helpful answer or clarification question.
- Never claim an action succeeded unless the action tool returned success.

TOOL SELECTION
- List channels: list_channel_tool
- Create a text channel: create_text_channel_tool
- Delete a text channel: delete_text_channel_tool
- Create a voice channel: create_voice_channel_tool
- Delete a voice channel: delete_voice_channel_tool
- List categories: list_category_tool
- Create, delete, or move a category: use the matching category tool
- List members or roles: use the matching list tool
- Create, assign, unassign, or delete a role: use the matching role tool
- Send a message: send_message_tool
- Find a message ID before deleting a message: get_message_history_tool

TOOL ARGUMENT CONTRACT
- Follow the exact allowed arguments for each tool. Never copy an ID from the
  context into another tool just because it is available.
- create_text_channel_tool and create_voice_channel_tool: guild_id, name, optional category_id.
- delete_text_channel_tool and delete_voice_channel_tool: guild_id, channel_id.
- list_channel_tool and list_category_tool: guild_id only.
- create_category_tool: guild_id, name. delete_category_tool: guild_id, category_id.
- move_category_tool: guild_id, category_id, position.
- send_message_tool: channel_id, content only. The context channel_id belongs to this tool.
- delete_message_tool: channel_id, message_id. get_message_history_tool: guild_id, channel_id, optional limit.
- list_member_tool and list_roles_tool: guild_id only.
- create_role_tool: guild_id, name, optional color_hex, hoist, preset.
- assign_role_tool and unassign_role_tool: guild_id, user_id, role_id.
- delete_role_tool: guild_id, role_id.
- Example: Never pass channel_id to create_text_channel_tool or create_voice_channel_tool.

CHANNEL CREATION
- If the user asks to create a text channel, call create_text_channel_tool.
- If the user asks to create a voice channel, call create_voice_channel_tool.
- If no category is requested, do not pass category_id.
- If the user provides a category ID, use that category_id.
- If the user provides a category name instead of an ID:
  1. Call list_category_tool.
  2. Find an exact matching category name.
  3. If exactly one category matches, call the create channel tool with its ID.
  4. If no category matches, tell the user that the category was not found.
  5. If multiple categories match, ask the user for the category ID.
- Never create a channel outside the requested category when the user explicitly requested one.

CHANNEL DELETION
- If the user gives only a channel name, call list_channel_tool and find an exact name and type match.
- Never delete immediately. The application displays the resolved channel names and IDs first,
  then waits for the user's confirmation.
- If no channel or multiple channels match, ask the user to clarify instead of deleting anything.
- Do not delete a text channel when the user requested a voice channel, or vice versa.
- Deletion requests are collected into one confirmation batch. Tell the user to confirm only
  after every requested deletion tool has been selected.

MESSAGE DELETION
- If the user asks to delete messages from a mentioned user in the current channel:
  1. Use guild_id and channel_id from the context. Never ask the user to provide them.
  2. Use the mentioned user's ID from the context. Never ask the user to provide it again.
  3. Call get_message_history_tool(guild_id, channel_id, limit=50).
  4. Select only messages whose author_id exactly matches the mentioned user's ID.
  5. Call delete_message_tool(channel_id, message_id) for every selected message in one batch.
  6. The application shows the matching messages before confirmation and deletes only after confirm.
- If no user is mentioned, ask the user to mention the target user.
- "All messages" means up to the 50 most recent messages because of the safety limit.

MULTIPLE COMMANDS
- When the user gives multiple independent commands in one message, call every matching action
  tool in the same response, in the order requested.
- For multiple deletion commands, call every matching delete tool in the same response. They are
  confirmed and executed together as one batch.

LIST RESULTS
- For channel, category, member, or role lists, show only a clean bullet list of names.
- Include an ID only when the user asks for it, when it is needed for the next step,
  or when there are duplicate names.
- Do not expose raw JSON to the user.

ERROR HANDLING
- If a tool returns an error, send that result to the user in a clear form.
- If required information is missing, ask one direct clarification question.
- Do not retry a destructive action automatically after an error.

EXAMPLES

User: "สร้างห้อง text ชื่อ general"
Flow:
1. create_text_channel_tool(guild_id, "general")

User: "สร้างห้องเสียงชื่อ meeting ใน category งาน"
Flow:
1. list_category_tool(guild_id)
2. Find category name "งาน"
3. create_voice_channel_tool(guild_id, "meeting", category_id)

User: "ลบห้อง test"
Flow:
1. list_channel_tool(guild_id)
2. Find the matching channel.
3. If exactly one match exists, delete it with the correct text or voice tool.

User: "แสดงรายการห้อง"
Flow:
1. list_channel_tool(guild_id)
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
client = ollama.AsyncClient()


def is_delete_all_messages_request(user_text: str) -> bool:
    """Identify explicit requests to delete every recent message in the current channel."""
    normalized_text = user_text.lower()
    return any(phrase in normalized_text for phrase in (
        "ลบทุกข้อความ",
        "ลบข้อความทั้งหมด",
        "delete all messages",
        "delete every message",
    ))


async def run_agent(user_text: str) -> str | None:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]
    nudged = False
    delete_all_messages = is_delete_all_messages_request(user_text)

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

        action_results = []
        confirmation_requested = False
        for call in res.message.tool_calls:
            name = call.function.name
            args = call.function.arguments or {}
            
            result = await execute_tool(name, args)

            if name == "get_message_history_tool" and delete_all_messages:
                try:
                    history = json.loads(result)
                except json.JSONDecodeError:
                    action_results.append("Error: Unable to read message history.")
                    continue

                if not isinstance(history, list):
                    action_results.append(str(result))
                    continue

                for message in history:
                    message_id = message.get("message_id")
                    if not message_id:
                        continue

                    deletion_result = await execute_tool("delete_message_tool", {
                        "channel_id": args["channel_id"],
                        "message_id": message_id,
                    })
                    if str(deletion_result).startswith("Confirmation required."):
                        confirmation_requested = True
                    else:
                        action_results.append(str(deletion_result))
                continue

            if str(result).startswith("Confirmation required."):
                confirmation_requested = True
                continue

            if name in MUTATING_TOOLS:
                action_results.append(str(result))
                continue

            # Standard tool role structure for Ollama API
            messages.append({
                "role": "tool",
                "content": str(result),
            })

        if confirmation_requested:
            context = request_context.get()
            pending_key = context if context else None
            deletions = pending_deletions[pending_key][0] if pending_key else []
            summary = "\n".join(action_results)
            confirmation = (
                "The following will be deleted:\n"
                f"{'\n'.join(deletion[2] for deletion in deletions)}\n"
                "Reply `confirm` or `ยืนยัน` within 5 minutes to continue."
            )
            return f"{summary}\n{confirmation}".strip()

        if action_results:
            return "\n".join(action_results)

    raise RuntimeError("Agent reached maximum execution step limit without finishing.")
