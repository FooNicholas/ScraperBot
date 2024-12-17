from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScraper(ABC):
    @abstractmethod
    async def fetch_page(self, url: str) -> str:
        """fetches page content from provided url."""
        pass

    @abstractmethod
    async def parse_cards(self, 
                           page_content: str, 
                           rarity: str, 
                           max_cards: int = 100
                          ) -> List[Dict[str, str]]:
        """
        parses cards from the page content based on criteria.
        
        arguments:
            page_content (str): HTML content in page
            rarity (str): specified rarity to search for 
            max_cards (int): maximum number to return
        
        returns:
            array of dictionaries containing card information
        """
        pass

    @abstractmethod
    def construct_url(self, set_number: str, rarity: str) -> str:
        """makes the url for the set number"""
        pass