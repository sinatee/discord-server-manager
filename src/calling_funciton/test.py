import os
from dotenv import load_dotenv
import discord

from server_info.list_member import list_member
from channel_and_mesaage.send_message import send_message
from member_and_role.create_role import create_role
from server_info.list_role import list_roles
from member_and_role.assign_role import assign_role
from member_and_role.unassign_role import unassign_role
from member_and_role.delete_role import delete_role

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

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

        guild_id = bot.get_guild(1552304569839780020)
        channel_id = bot.get_channel(1558820517929164840)
        role_id = 1558819283243630702
        user_id = 1557395724319072366

        res = await delete_role(
            guild=guild_id,
            role_id=role_id
        )
        await send_message(channel_id, res)

if __name__ == '__main__':
    bot = Bot()
    bot.run(DISCORD_TOKEN)