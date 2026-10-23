_bot_instance = None

def set_bot(bot_obj):
    global _bot_instance
    _bot_instance = bot_obj

def get_bot():
    return _bot_instance
