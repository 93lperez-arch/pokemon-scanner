import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, urlunsplit
import time
import threading

WEBHOOK = os.getenv("DISCORD_WEBHOOK")

SCAN_INTERVAL = 4

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

EXCLUDE = [
"journey together"
]

HEADERS = {
"User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(HEADERS)

def clean_url(url):
parts = urlsplit(url)
return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

def send_alert(product):

```
if not WEBHOOK:
    print("Missing DISCORD_WEBHOOK secret")
    return

payload = {
    "content": f"🚨 **{product['title']}**\n{product['url']}\nStore: {product['retailer']}"
}

try:
    session.post(WEBHOOK, json=payload, timeout=10)
except:
    pass
```

def fetch(url):

```
try:
    r = session.get(url, timeout=20)
    return r.text
except:
    return ""
```

def scan_retailer(retailer, url):

```
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

    full_url = clean_url(urljoin(url, href))

    products.append({
        "title": title,
        "url": full_url,
        "retailer": retailer
    })

return products
```

seen = set()

print("Pokemon TCG Drop Bot Running")

def run_bot():

```
global seen

while True:

    for retailer, url in RETAILERS.items():

        try:

            products = scan_retailer(retailer, url)

            for product in products:

                if product["url"] in seen:
                    continue

                seen.add(product["url"])

                send_alert(product)

                print("ALERT:", product["title"])

        except Exception as e:

            print("Error:", retailer, e)

    time.sleep(SCAN_INTERVAL)
```

thread = threading.Thread(target=run_bot)
thread.daemon = True
thread.start()

while True:
time.sleep(60)
