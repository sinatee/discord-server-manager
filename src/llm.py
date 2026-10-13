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


SYSTEM_PROMPT = """You manage a Discord server by calling tools.
- Use tools to look up information or make changes.
- Never invent IDs. Copy them from the message context.
- When you are done, reply with a short plain-text summary of what you did or found."""

LOOP_LIMIT = 7
client = ollama.AsyncClient()

async def run_agent(user_text: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]
    for _ in range(LOOP_LIMIT):
        res = await client.chat(
            model="qwen2.5:1.5b",
            messages=messages,
            tools=TOOLS,
            keep_alive="10m",
            options={
                "temperature": 0,
                "num_ctx": 4096,
                "num_predict": 300,
            },
        )

        if res.done_reason == "length":
            return "Error: the reply was cut off. Try a shorter request."

        messages.append(res.message)

        if not res.message.tool_calls:
            return res.message.content or "(no reply)"

        for call in res.message.tool_calls:
            result = await execute_tool(call.function.name, call.function.arguments)
            messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})

    return "Stopped: too many steps."
