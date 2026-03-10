import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

WEBHOOK = os.getenv("DISCORD_WEBHOOK")

SCAN_INTERVAL = 5

RETAILERS = {
"pokemon_center": "https://www.pokemoncenter.com/category/trading-card-game",
"target": "https://www.target.com/s?searchTerm=pokemon+trading+card+game",
"walmart": "https://www.walmart.com/search?q=pokemon+trading+card+game",
"bestbuy": "https://www.bestbuy.com/site/searchpage.jsp?st=pokemon+trading+card+game",
"gamestop": "https://www.gamestop.com/search/?q=pokemon+tcg",
"samsclub": "https://www.samsclub.com/s/pokemon",
"costco": "https://www.costco.com/CatalogSearch?keyword=pokemon"
}

KEYWORDS = [
"elite trainer box",
"etb",
"booster bundle",
"tech sticker",
"collection box"
]

EXCLUDE = ["journey together"]

HEADERS = {"User-Agent": "Mozilla/5.0"}

session = requests.Session()

def fetch(url):
try:
r = session.get(url, headers=HEADERS, timeout=20)
return r.text
except:
return ""

def scan_store(store, url):

html = fetch(url)

if not html:
    return []

soup = BeautifulSoup(html, "html.parser")

products = []

for link in soup.select("a[href]"):

    title = link.get_text(strip=True)

    if not title:
        continue

    title_lower = title.lower()

    if not any(k in title_lower for k in KEYWORDS):
        continue

    if any(b in title_lower for b in EXCLUDE):
        continue

    href = link.get("href")

    if not href:
        continue

    full_url = urljoin(url, href)

    products.append((title, full_url))

return products

seen = set()

print("Pokemon bot running")

while True:

for store, url in RETAILERS.items():

    try:

        products = scan_store(store, url)

        for title, link in products:

            if link in seen:
                continue

            seen.add(link)

            if WEBHOOK:
                payload = {
                    "content": f"🚨 {title}\n{link}\nStore: {store}"
                }
                try:
                    session.post(WEBHOOK, json=payload, timeout=10)
                except:
                    pass

            print("ALERT:", title)

    except Exception as e:

        print("Error:", store, e)

time.sleep(SCAN_INTERVAL)
