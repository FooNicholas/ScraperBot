import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    ConversationHandler, 
    filters, 
    CallbackContext
)

from scrapers.yuyutei.yuyutei_scraper import YuyuTeiScraper
from scrapers.bigweb.bigweb_scraper import BigWebScraper
from services.translation_service import TranslationService
from utils.error_handling import (
    log_error, 
    ScraperError, 
    NetworkError, 
    ParseError
)

from dotenv import load_dotenv

load_dotenv()

#configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

translation_service = TranslationService()

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
BIGWEB_MAPPING_FILE = os.path.join(BASE_DIR, "scrapers", "bigweb", "bigweb_mapping.json")

scrapers = {
    'yuyutei': YuyuTeiScraper(translator=translation_service),
    'bigweb': BigWebScraper(mapping_file=BIGWEB_MAPPING_FILE,translator=translation_service)
}

#states for conversation handler
SITE, SET_NUMBER, RARITY = range(3)

#on startup / shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):

    try:
        bot_application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        #setup conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                SITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_site)],
                SET_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_set_number)],
                RARITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rarity)]
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )
        
        bot_application.add_handler(conv_handler)
        
        await bot_application.initialize()
        await bot_application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        
        app.state.bot_application = bot_application
        
        yield
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

app = FastAPI(lifespan=lifespan)

#telegrambot handlers
async def start(update: Update, context: CallbackContext):
    
    await update.message.reply_text(
        "Welcome! One reply at a time please. Please choose a site:\n"
        "Available sites: yuyutei, bigweb"
    )
    return SITE

async def handle_site(update: Update, context: CallbackContext):
    
    site = update.message.text.lower().strip()
    
    if site not in scrapers:
        await update.message.reply_text(
            "Invalid site. Please choose from: " + 
            ", ".join(scrapers.keys())
        )
        return SITE
    
    context.user_data['site'] = site
    await update.message.reply_text("Enter the set number (e.g. dzbt01):")
    return SET_NUMBER

async def handle_set_number(update: Update, context: CallbackContext):

    set_number = update.message.text.strip().upper()
    context.user_data['set_number'] = set_number
    await update.message.reply_text("Enter the rarity (e.g. FFR):")
    return RARITY

async def handle_rarity(update: Update, context: CallbackContext):

    site = context.user_data['site']
    set_number = context.user_data['set_number']
    rarity = update.message.text.strip().upper()
    
    try:
        loading_message = await update.message.reply_text("Loading...")
        scraper = scrapers[site]
        url = scraper.construct_url(set_number, rarity)
        page_content = await scraper.fetch_page(url)
        cards = await scraper.parse_cards(page_content, rarity)
        
        if not cards:
            await loading_message.edit_text("No cards found.")
        else:
            result = "\n".join(
                f"{card['name']}: {card['price']}" for card in cards
            )
            await loading_message.edit_text(result)
    
    except Exception as e:
        log_error(e)
        await update.message.reply_text(
            "An error occurred while processing your request."
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):

    await update.message.reply_text(
        "Operation cancelled. You can start again by typing /start."
    )
    return ConversationHandler.END

#Endpoints
@app.post("/webhook")
async def handle_webhook(request: Request):

    try:
        update = Update.de_json(await request.json(), app.state.bot_application.bot)
        await app.state.bot_application.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        log_error(e)
        return JSONResponse(
            status_code=500, 
            content={"error": "Webhook processing failed"}
        )

@app.get("/")
def read_root():
    return {"message": "Telegram Scraper Bot is running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)