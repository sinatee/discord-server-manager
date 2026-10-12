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

    # actvate when received message
    async def on_message(self, message: discord.Message):
        # Ignore bot messages
        if message.author.bot:
            return

         # Check if this bot is mentioned
        if self.user not in message.mentions:
            return
        
        # Ignore DMs
        if not message.guild:
            return
        
        clean_message = (
            message.content
            .replace(f"<@{self.user.id}>", "")
            .replace(f"<@!{self.user.id}>", "")
            .strip()
        )

        #If the user tagged the bot with no message 
        if not clean_message:
            await message.reply("pen kuy rai?")
            return

        context_data = "\n".join([
            "[Message Context]",
            f"Server: {message.guild.name} (ID: {message.guild.id})",
            f"Channel: {message.channel.name} (ID: {message.channel.id})",
            f"User: {message.author.display_name} (ID: {message.author.id})",
            f"User Message: {clean_message}",
        ])
        

if __name__ == '__main__':
    if not DISCORD_TOKEN:
        raise ValueError("Error: DISCORD_TOKEN is missing in .env")
    bot = Bot()
    bot.run(DISCORD_TOKEN)
