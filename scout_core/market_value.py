import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import inspect
from functools import lru_cache

def get_market_value(player_name):
    """
    Searches for 'player_name' in Transfermarket and returns his market value
    """
    base_url = "https://www.transfermarkt.pt/schnellsuche/ergebnis/schnellsuche"
    ua = UserAgent()

    headers = {
        'User-Agent': ua.random
    }

    params = {
        'query': player_name
    }

    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        row = soup.select_one("table.items > tbody > tr")

        if not row:
            print(f"Nenhum resultado para: {player_name}")
            return None

        cells = row.select("td")
        
        # Procurar a primeira célula que contenha "M €"
        for cell in cells:
            text = cell.get_text(strip=True)
            if "M €" in text:
                time.sleep(1)  # sleep após sucesso para não ser bloqueado
                return text

        print(f"Valor de mercado não encontrado para: {player_name}")
        return None

    except Exception as e:
        print(f"Erro ao processar {player_name}: {e}")
        return None

@lru_cache(maxsize=4096)
def cached_market_value(name: str):
    try:
        return get_market_value(name)
    except Exception:
        return None