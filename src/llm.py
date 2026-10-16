import inspect

import ollama

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

async def execute_tool(tool_name: str, arguments: dict) -> str:
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
- Always use the guild_id from the context for server actions.
- Always use the channel_id from the context when calling send_message_tool.
- Never invent, guess, or use placeholder IDs.

RESPONSE RULE
- Every user request must end with send_message_tool.
- For an action request: call the required action tool first, then call
  send_message_tool with the real result returned by that tool.
- For a question or an ambiguous request: call send_message_tool with a helpful answer
  or a clarification question.
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
- Delete actions require a channel_id.
- If the user gives a channel ID, use it with the matching delete tool.
- If the user gives only a channel name:
  1. Call list_channel_tool.
  2. Find an exact matching channel name and type.
  3. If exactly one match exists, delete it with the matching delete tool.
  4. If no match exists, report that it was not found.
  5. If multiple matches exist, ask the user to provide the channel ID.
- Do not delete a text channel when the user requested a voice channel, or vice versa.

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
2. send_message_tool(channel_id, tool result)

User: "สร้างห้องเสียงชื่อ meeting ใน category งาน"
Flow:
1. list_category_tool(guild_id)
2. Find category name "งาน"
3. create_voice_channel_tool(guild_id, "meeting", category_id)
4. send_message_tool(channel_id, tool result)

User: "ลบห้อง test"
Flow:
1. list_channel_tool(guild_id)
2. Find the matching channel.
3. If exactly one match exists, delete it with the correct text or voice tool.
4. send_message_tool(channel_id, tool result)

User: "แสดงรายการห้อง"
Flow:
1. list_channel_tool(guild_id)
2. send_message_tool(channel_id, formatted list)
"""

LOOP_LIMIT = 10
CHANNEL_DELETE_TOOLS = {"delete_text_channel_tool", "delete_voice_channel_tool"}
client = ollama.AsyncClient()

async def run_agent(user_text: str) -> None:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]
    sent = False
    nudged = False

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
            if sent:
                print(f"[agent done] {res.message.content}")
                return
            
            if not nudged:
                nudged = True
                messages.append({
                    "role": "user",
                    "content": "REMINDER: You must call `send_message_tool` to reply. The user cannot see plain text. Call `send_message_tool` now.",
                })
                continue

            raise RuntimeError("model never sent a message")

        for call in res.message.tool_calls:
            name = call.function.name
            args = call.function.arguments or {}
            
            result = await execute_tool(name, args)

            if (
                name in CHANNEL_DELETE_TOOLS
                and not str(result).startswith("Error")
            ):
                print(f"[agent done] {name} completed.")
                return
            
            if name == "send_message_tool" and not str(result).startswith("Error"):
                sent = True
                print("[agent done] Reply sent.")
                return

            # Standard tool role structure for Ollama API
            messages.append({
                "role": "tool",
                "content": str(result),
            })

    raise RuntimeError("Agent reached maximum execution step limit without finishing.")
