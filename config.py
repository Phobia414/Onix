import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0").strip())

# Правильная обработка CHANNEL_ID (для приватных каналов -100...)
_channel_raw = os.getenv("CHANNEL_ID", "").strip()
if _channel_raw.lstrip('-').isdigit():
    CHANNEL_ID = int(_channel_raw)
else:
    CHANNEL_ID = _channel_raw