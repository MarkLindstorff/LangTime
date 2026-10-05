import requests

LIBRETRANSLATE_URL = "http://127.0.0.1:5001"

def translate_text(text: str, source: str = "ru", target: str = "da") -> str:
    """Oversætter en vilkårlig tekst via LibreTranslate (ord ELLER sætning)."""
    response = requests.post(
        f"{LIBRETRANSLATE_URL}/translate",
        json={"q": text, "source": source, "target": target},
        timeout=10,  # længere timeout — sætninger tager lidt længere end ord
    )
    response.raise_for_status()
    return response.json()["translatedText"]

def translate_word(word: str, source: str = "ru", target: str = "da") -> str:
    """Oversætter et enkelt ord — specialtilfælde af translate_text."""
    return translate_text(word, source, target)