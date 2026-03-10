import os
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

WEBHOOK = os.getenv("DISCORD_WEBHOOK")
SCAN_INTERVAL = 5

RETAILERS = {
    "pokemon_center": "https://www.pokemoncenter.com/category/trading-card-game",
    "target": "https://www.target.com/s?searchTerm=pokemon+trading+card+game",
    "walmart": "https://www.walmart.com/search?q=pokemon+trading+card+game",
    "bestbuy": "https://www.bestbuy.com/site/searchpage.jsp?st=pokemon+trading+card+game",
    "gamestop": "https://www.gamestop.com/search/?q=pokemon+tcg",
    "samsclub": "https://www.samsclub.com/s/pokemon",
    "costco": "https://www.costco.com/CatalogSearch?keyword=pokemon",
}

KEYWORDS = [
    "elite trainer box",
    "etb",
    "booster bundle",
    "tech sticker",
    "collection box",
]

EXCLUDE = ["journey together"]

HEADERS = {"User-Agent": "Mozilla/5.0"}

session = requests.Session()

print("Pokemon bot running")

seen = set()

while True:
    for store, url in RETAILERS.items():
        try:
            response = session.get(url, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(response.text, "html.parser")

            for link in soup.select("a[href]"):
                title = link.get_text(strip=True)
                if not title:
                    continue

                title_lower = title.lower()

                if not any(keyword in title_lower for keyword in KEYWORDS):
                    continue

                if any(bad in title_lower for bad in EXCLUDE):
                    continue

                href = link.get("href")
                if not href:
                    continue

                full_url = urljoin(url, href)

                if full_url in seen:
                    continue

                seen.add(full_url)

                if WEBHOOK:
                    payload = {
                        "content": f"🚨 {title}\n{full_url}\nStore: {store}"
                    }
                    try:
                        session.post(WEBHOOK, json=payload, timeout=10)
                    except Exception:
                        pass

                print("ALERT:", title)

        except Exception as e:
            print("Error:", store, e)

    time.sleep(SCAN_INTERVAL)
