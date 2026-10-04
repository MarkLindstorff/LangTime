import requests

LIBRETRANSLATE_URL = "http://127.0.0.1:5001"

def translate_word(word: str, source: str = "ru", target: str = "da") -> str:
    """Oversætter et enkelt ord via LibreTranslate."""
    response = requests.post(
        f"{LIBRETRANSLATE_URL}/translate",
        json={"q": word, "source": source, "target": target},
        timeout=5,
    )
    response.raise_for_status()  # smider en fejl hvis serveren svarer med 4xx/5xx
    return response.json()["translatedText"]