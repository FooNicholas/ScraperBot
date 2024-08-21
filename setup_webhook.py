import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")

print(response.json())