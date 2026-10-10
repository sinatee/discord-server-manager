import os
from dotenv import load_dotenv
import discord

from server_info.list_member import list_member
from chanel_and_mesaage.send_message import send_message

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

        server = self.get_guild(1552304569839780020)
        channel = self.get_channel(ALLOWED_CHANNEL_ID)
        res = await list_member(server)
        print(res)
        print(await send_message(channel, res))


if __name__ == '__main__':
    bot = Bot()
    bot.run(DISCORD_TOKEN)