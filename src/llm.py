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

async def execute_tool(tool_name: str, arguments: dict) -> str:
    """Dynamically execute a tool function by name with given arguments."""

    print(f"[tool call] {tool_name} {dict(arguments)}")

    if tool_name not in AVAILABLE_TOOLS:
        return f"Error: Tool '{tool_name}' not found."
    
    tool_func = AVAILABLE_TOOLS[tool_name]
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
            model="qwen2.5:1.5b",
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
            
            if name == "send_message_tool" and not str(result).startswith("Error"):
                sent = True

            # Standard tool role structure for Ollama API
            messages.append({
                "role": "tool",
                "content": str(result),
            })

    raise RuntimeError("Agent reached maximum execution step limit without finishing.")
