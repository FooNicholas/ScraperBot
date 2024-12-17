import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..base_scraper import BaseScraper
from services.translation_service import TranslationService
from typing import List, Dict

class BigWebScraper(BaseScraper):
    def __init__(self, mapping_file: str, translator: TranslationService):
        self.mapping_file = mapping_file
        self.set_to_url_mapping = self.load_mapping()
        self.translator = translator

    def load_mapping(self) -> Dict[str, str]:
        try:
            with open(self.mapping_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading mapping file: {e}")
            return {}

    def construct_url(self, set_number: str, rarity: str) -> str:
        url_number = self.set_to_url_mapping.get("set_numbers", {}).get(set_number)
        rarity_number = self.set_to_url_mapping.get("rarity_numbers", {}).get(rarity)

        if not url_number:
            raise ValueError(f"No URL mapping found for set number: {set_number}")
        if not rarity_number:
            raise ValueError(f"No URL mapping found for rarity: {rarity}")

        return f"https://www.bigweb.co.jp/ja/products/vg/list?cardsets={url_number}&rarity={rarity_number}&is_box=0"

    async def fetch_page(self, url: str) -> str:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(service=Service(), options=options)

        try:
            print("Loading the webpage...")
            driver.get(url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[starts-with(@href, '/ja/products/vg/cardViewer/')]"))
            )

            page_content = driver.page_source
            return page_content
        finally:
            driver.quit()

    async def parse_cards(self, page_content: str, rarity: str, max_cards: int = 100) -> List[Dict]:
        soup = BeautifulSoup(page_content, "html.parser")
        card_list = []

        card_name_elements = soup.find_all("a", href=lambda x: x and x.startswith("/ja/products/vg/cardViewer/"))

        for card_name_element in card_name_elements[:max_cards]:
            shared_class_suffix = [cls for cls in card_name_element.get("class", []) if "ng-tns" in cls]
            if not shared_class_suffix:
                continue

            shared_class_suffix = shared_class_suffix[0]
            card_name = card_name_element.get_text(strip=True)
            translated_name = self.translator.translate(card_name)

            # Find the price with the same shared class suffix
            price_element = soup.find("span", class_=lambda x: x and shared_class_suffix in x and "item-product-price" in x)
            card_price = price_element.get_text(strip=True) if price_element else "Sold Out"

            card_list.append({
                "name": translated_name,
                "price": card_price
            })

        return card_list
