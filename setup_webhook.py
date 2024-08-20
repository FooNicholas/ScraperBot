import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = f"https://cardboard-scraper.vercel.app/api/bot"

def set_webhook():
    response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}")
    print(response.json())

if __name__ == "__main__":
    set_webhook()