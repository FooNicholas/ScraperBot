import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from ..base_scraper import BaseScraper
from typing import List, Dict

class YuyuTeiScraper(BaseScraper):
    def __init__(self, translator=None):
        self.translator = GoogleTranslator(source="ja", target="en")

    def construct_url(self, set_number: str, rarity: str) -> str:
        return f"https://yuyu-tei.jp/sell/vg/s/{set_number}"

    async def fetch_page(self, url: str) -> str:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch page: {e}")

    async def parse_cards(self, 
                           page_content: str, 
                           rarity: str, 
                           max_cards: int = 100
                          ) -> List[Dict[str, str]]:
        soup = BeautifulSoup(page_content, "html.parser")
        results = soup.find(class_="col-12 mb-5 pb-5")
        
        if not results:
            return []

        rarity_containers = results.find_all(class_="py-4 cards-list")
        
        for container in rarity_containers:
            found_rarity = container.find("span", class_="py-2 d-inline-block px-2 me-2 text-white fw-bold")
            if found_rarity and found_rarity.text == rarity:
                card_list = container.find_all("div", class_="col-md")
                break
        else:
            return []

        cards = []
        for card in card_list[:max_cards]:
            card_name = card.find("h4", class_="text-primary fw-bold").text.strip()
            card_price = card.find("strong", class_="d-block text-end").text.strip()
            
            translated_name = self.translator.translate(card_name)
            
            cards.append({
                "name": translated_name,
                "price": card_price
            })
        
        return cards

    