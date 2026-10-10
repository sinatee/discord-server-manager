import os
from dotenv import load_dotenv
import discord

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ALLOWED_CHANNEL_ID = os.getenv("ALLOWED_CHANNEL_ID")
ALLOWED_CHANNEL_ID = int(ALLOWED_CHANNEL_ID) if ALLOWED_CHANNEL_ID else None

class Bot(discord.Client):

    def __init__(self):
        request_data = discord.Intents.default()
        request_data.message_content = True
        request_data.members = True
        request_data.guilds = True
        super().__init__(intents=request_data)

    # activate on succesfully connect to  discord server
    async def on_ready(self):
        print(f"[Bot] Logged in as: {self.user} (ID: {self.user.id})")
        if ALLOWED_CHANNEL_ID:
            print(f"[Bot] Listening strictly to channel ID: {ALLOWED_CHANNEL_ID}")
        else:
            print("[Bot] Warning: ALLOWED_CHANNEL_ID is not set!")
        print("[Bot] Ready to receive messages.")

    # actvate when received message
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        if ALLOWED_CHANNEL_ID and (message.channel.id != ALLOWED_CHANNEL_ID):
            return

        print(f"[Received] From {message.author.name}: {message.content}")
        await message.reply(f"{message.content}")

if __name__ == '__main__':
    if not DISCORD_TOKEN:
        raise ValueError("Error: DISCORD_TOKEN is missing in .env")
    bot = Bot()
    bot.run(DISCORD_TOKEN)
