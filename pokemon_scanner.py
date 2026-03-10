import os
import time
import requests

WEBHOOK = os.getenv("DISCORD_WEBHOOK")

HEADERS = {"User-Agent": "Mozilla/5.0"}

URLS = [
("pokemon_center","https://www.pokemoncenter.com/category/trading-card-game"),
("target","https://www.target.com/s?searchTerm=pokemon+trading+card+game"),
("walmart","https://www.walmart.com/search?q=pokemon+trading+card+game"),
("bestbuy","https://www.bestbuy.com/site/searchpage.jsp?st=pokemon+trading+card+game"),
("gamestop","https://www.gamestop.com/search/?q=pokemon+tcg"),
("samsclub","https://www.samsclub.com/s/pokemon"),
("costco","https://www.costco.com/CatalogSearch?keyword=pokemon")
]

KEYWORDS = ["elite trainer box","etb","booster bundle","tech sticker","collection box"]
EXCLUDE = ["journey together"]

session = requests.Session()

seen = set()

print("Pokemon bot running")

while True:

for store, url in URLS:

    try:

        r = session.get(url, headers=HEADERS, timeout=20)

        text = r.text.lower()

        if not any(k in text for k in KEYWORDS):
            continue

        if any(b in text for b in EXCLUDE):
            continue

        if url in seen:
            continue

        seen.add(url)

        print("ALERT:", store)

        if WEBHOOK:
            payload = {
                "content": "🚨 Pokemon product detected\n" + url + "\nStore: " + store
            }

            try:
                session.post(WEBHOOK, json=payload, timeout=10)
            except:
                pass

    except Exception as e:

        print("Error:", store, e)

time.sleep(5)
