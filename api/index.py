import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import logging
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters, CallbackContext

from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import requests

from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

application = ApplicationBuilder().token(BOT_TOKEN).build()

translator = GoogleTranslator(source="ja", target="en")

rarity, set_number = range(2)

#Pydantic model for Telegram webhook data
class TelegramWebhook(BaseModel):
    update_id: int
    message: Optional[dict]
    edited_message: Optional[dict]
    channel_post: Optional[dict]
    edited_channel_post: Optional[dict]
    inline_query: Optional[dict]
    chosen_inline_result: Optional[dict]
    callback_query: Optional[dict]
    shipping_query: Optional[dict]
    pre_checkout_query: Optional[dict]
    poll: Optional[dict]
    poll_answer: Optional[dict]

# Telegram command handlers
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Please enter the set number (e.g., dzbt01):")
    return set_number

async def handle_set_number(update: Update, context: CallbackContext):
    context.user_data['set_number'] = update.message.text.strip().upper()
    await update.message.reply_text("Please enter the rarity (e.g., FFR):")
    return rarity

async def handle_rarity(update: Update, context: CallbackContext):
    context.user_data['rarity'] = update.message.text.strip().upper()
    set_number = context.user_data['set_number']
    rarity = context.user_data['rarity']
    await update.message.reply_text(f"Searching for cards with rarity: {rarity} in set_number: {set_number}")
    result = get_cards_by_rarity(rarity, set_number)
    await update.message.reply_text(result)
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Operation cancelled. You can start again by typing /start.")
    return ConversationHandler.END

# Register command handlers
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        set_number: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_set_number)],
        rarity: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rarity)]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
application.add_handler(conv_handler)

@app.post("/webhook")
async def telegram_webhook(webhook_data: TelegramWebhook):
    try:
        logger.info(f"Received webhook data: {webhook_data.dict()}")
        update = Update.de_json(webhook_data.dict(), application.bot)
        logger.info(f"Deserialized update object: {update}")
        await application.update_queue.put(update)
        return {"message": "ok"}
    
    except Exception as e:
        logger.error(f"Error processing update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error processing webhook: {str(e)}")
        
@app.get("/")
def index():
    return {"message": "Hello, World!"}

def fetch(url):
    response = requests.get(url)
    return response.text

def translate_card_name(card_name):
    return translator.translate(card_name)

def get_cards_by_rarity(rarity, set_number):
    URL = f"https://yuyu-tei.jp/sell/vg/s/{set_number}"
    page_content = fetch(URL)
    soup = BeautifulSoup(page_content, "html.parser")
    results = soup.find(class_="col-12 mb-5 pb-5")
    rarity_containers = results.find_all(class_="py-4 cards-list")
    card_list = []
    for container in rarity_containers:
        found_rarity = container.find("span", class_="py-2 d-inline-block px-2 me-2 text-white fw-bold")
        if found_rarity.text == rarity:
            card_list = container.find_all("div", class_="col-md")
            break
    card_names = []
    card_prices = []
    for card in card_list:
        card_name = card.find("h4", class_="text-primary fw-bold").text.strip()
        card_price = card.find("strong", class_="d-block text-end").text.strip()
        card_names.append(card_name)
        card_prices.append(card_price)
    translated_names = [translate_card_name(name) for name in card_names]
    result = "\n".join(f"{translated_name}: {card_price}" for translated_name, card_price in zip(translated_names, card_prices))
    return result if result else "No cards found."