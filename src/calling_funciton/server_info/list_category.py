import json
import discord

async def list_category(guild : discord.Guild) -> str :
    if guild is None :
        return json.dumps({"error" : "Guild not found."})

    categories_data = []

    for category in guild.categories :
        categories_data.append({
            "id" : str(category.id) ,
            "name" : category.name ,
            "position" : category.position ,
        })

    return json.dumps(
        categories_data ,
        ensure_ascii = False ,
        indent = 2 ,
    )