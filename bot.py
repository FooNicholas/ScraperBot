import aiohttp
import asyncio
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source="ja", target="en")
URL = "https://yuyu-tei.jp/sell/vg/s/dzbt01"

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def translate_card_name(card_name):
    return translator.translate(card_name)

async def main():
    async with aiohttp.ClientSession() as session:
        page_content = await fetch(session, URL)
        soup = BeautifulSoup(page_content, "html.parser")

        results = soup.find(class_="col-12 mb-5 pb-5")
        rarity_containers = results.find_all(class_="py-4 cards-list")

        card_list = []
        for container in rarity_containers:
            rarity = container.find("span", class_="py-2 d-inline-block px-2 me-2 text-white fw-bold")
            if rarity.text == 'SR':
                card_list = container.find_all("div", class_="col-md")
                break

        card_names = []
        card_prices = []

        for card in card_list:
            card_name = card.find("h4", class_="text-primary fw-bold").text.strip()
            card_price = card.find("strong", class_="d-block text-end").text.strip()
            card_names.append(card_name)
            card_prices.append(card_price)

        translated_names = await asyncio.gather(*[translate_card_name(name) for name in card_names])

        for translated_name, card_price in zip(translated_names, card_prices):
            print(f"{translated_name}: {card_price}")

asyncio.run(main())