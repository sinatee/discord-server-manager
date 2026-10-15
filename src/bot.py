import discord
from llm import run_agent
from client_state import set_bot
# import os
# from dotenv import load_dotenv

# load_dotenv()

# DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
# ALLOWED_CHANNEL_ID = os.getenv("ALLOWED_CHANNEL_ID")
# ALLOWED_CHANNEL_ID = int(ALLOWED_CHANNEL_ID) if ALLOWED_CHANNEL_ID else None

class Bot(discord.Client):

    def __init__(self):
        request_data = discord.Intents.default()
        request_data.message_content = True
        request_data.members = True
        request_data.guilds = True
        super().__init__(intents=request_data)
        set_bot(self)

    # activate on succesfully connect to  discord server
    async def on_ready(self):
        print(f"[Bot] Logged in as: {self.user} (ID: {self.user.id})")

    # actvate when received message
    async def on_message(self, message: discord.Message):
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Ignore DMs
        if not message.guild:
            return

        bot_id_str = str(self.user.id)
        raw_content = message.content

         # Check if this bot is mentioned
        is_mentioned = (
            self.user in message.mentions
            or f"<@{bot_id_str}>" in raw_content
            or f"<@!{bot_id_str}>" in raw_content
            or "@server-manager" in raw_content.lower()
            or (message.guild and any(role.name.lower() == "server-manager" for role in message.role_mentions))
        )

        if not is_mentioned:
            return
        
        
        import re
        clean_message = re.sub(r"<@&?\d+>", "", raw_content) # removes <@ID> and <@&ID>
        clean_message = re.sub(r"@server-manager", "", clean_message, flags=re.IGNORECASE)
        clean_message = clean_message.strip()


        print(f"[DEBUG RAW]: {repr(message.content)}")
        print(f"[DEBUG CLEAN]: {repr(clean_message)}")

        #If the user tagged the bot with no message 
        if not clean_message:
            await message.reply("arai?")
            return

        context_data = "\n".join([
            "[Message Context]",
            f"Server: {message.guild.name} (ID: {message.guild.id})",
            f"Channel: {message.channel.name} (ID: {message.channel.id})",
            f"User: {message.author.display_name} (ID: {message.author.id})",
            f"User Message: {clean_message}",
            "",
            f"REMINDER: You must reply by calling send_message_tool(channel_id='{message.channel.id}', content=...).",
        ])

        try:
            async with message.channel.typing():
                await run_agent(context_data)
        except Exception as e:
            print(f"[Bot] LLM error: {e}")
            await message.reply("Something went wrong talking to the model.")

