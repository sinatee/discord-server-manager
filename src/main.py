import os
from dotenv import load_dotenv
from bot import bot

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("Error: DISCORD_TOKEN is missing in .env")
    bot.run(DISCORD_TOKEN)