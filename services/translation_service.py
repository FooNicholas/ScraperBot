from deep_translator import GoogleTranslator
from functools import lru_cache
from typing import Optional

class TranslationService:

    def __init__(self, 
                 source_lang: str = 'ja', 
                 target_lang: str = 'en'):

        self.translator = GoogleTranslator(
            source=source_lang, 
            target=target_lang
        )
    
    @lru_cache(maxsize=1000)
    def translate(self, text: str) -> str:
        
        if not text:
            return ""
        
        try:
            return self.translator.translate(text)
        except Exception as e:
            
            return text  #fallback returns jp text on failure
    
    
    def batch_translate(self, texts: list[str]) -> list[str]:
        
        return [self.translate(text) for text in texts]