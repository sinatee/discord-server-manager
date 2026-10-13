import ollama
from tool.get_roles import get_roles

messages = [{"role": "user", "content": "Please check the roles in server ID 987654321."}]

response = ollama.chat(model="qwen2.5:1.5b", messages=messages, tools=[get_roles], keep_alive=0)

if response.message.tool_calls:
    messages.append(response.message)          # keep the model's tool request

    for call in response.message.tool_calls:
        result = get_roles(**call.function.arguments)    # YOUR code runs the function
        print(call.function.arguments)
        print(result)
        messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})
        print(messages)

    # final = ollama.chat(model="qwen2.5:1.5b", messages=messages, keep_alive=0)
    # print(final.message.content)               # now it's a normal text answer