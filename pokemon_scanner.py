import time
import requests
import os
import re
from datetime import datetime
from urllib.parse import urljoin

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

CHECK_INTERVAL = 10
TIMEOUT = 20

WALMART_CART_URL = "https://www.walmart.com/cart"
WALMART_CHECKOUT_URL = "https://www.walmart.com/checkout"
WALMART_BASE = "https://www.walmart.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}

# Known direct product pages
PRODUCTS = [
    {
        "name": "Prismatic Evolutions ETB",
        "url": "https://www.walmart.com/ip/13816151308",
        "site": "product",
    },
    {
        "name": "Prismatic Evolutions Booster Bundle",
        "url": "https://www.walmart.com/ip/5373472869",
        "site": "product",
    },
    {
        "name": "Pokemon 151 Booster Bundle",
        "url": "https://www.walmart.com/ip/1160437186",
        "site": "product",
    },
    {
        "name": "Surging Sparks ETB",
        "url": "https://www.walmart.com/ip/10692607747",
        "site": "product",
    },
]

# Search pages for discovery + stock-ish signals
SEARCHES = [
    {
        "name": "Perfect Order ETB Search",
        "url": "https://www.walmart.com/search?q=pokemon+perfect+order+elite+trainer+box",
    },
    {
        "name": "Perfect Order Booster Box Search",
        "url": "https://www.walmart.com/search?q=pokemon+perfect+order+booster+box",
    },
    {
        "name": "Perfect Order Booster Bundle Search",
        "url": "https://www.walmart.com/search?q=pokemon+perfect+order+booster+bundle",
    },

    {
        "name": "Phantasmal Flames ETB Search",
        "url": "https://www.walmart.com/search?q=phantasmal+flames+elite+trainer+box",
    },
    {
        "name": "Phantasmal Flames Booster Box Search",
        "url": "https://www.walmart.com/search?q=phantasmal+flames+booster+box",
    },
    {
        "name": "Phantasmal Flames Booster Bundle Search",
        "url": "https://www.walmart.com/search?q=phantasmal+flames+booster+bundle",
    },

    {
        "name": "Destined Rivals ETB Search",
        "url": "https://www.walmart.com/search?q=pokemon+destined+rivals+elite+trainer+box",
    },
    {
        "name": "Destined Rivals Booster Box Search",
        "url": "https://www.walmart.com/search?q=pokemon+destined+rivals+booster+box",
    },
    {
        "name": "Destined Rivals Booster Bundle Search",
        "url": "https://www.walmart.com/search?q=pokemon+destined+rivals+booster+bundle",
    },

    {
        "name": "Black Bolt ETB Search",
        "url": "https://www.walmart.com/search?q=pokemon+black+bolt+elite+trainer+box",
    },
    {
        "name": "Black Bolt Booster Box Search",
        "url": "https://www.walmart.com/search?q=pokemon+black+bolt+booster+box",
    },
    {
        "name": "Black Bolt Booster Bundle Search",
        "url": "https://www.walmart.com/search?q=pokemon+black+bolt+booster+bundle",
    },
    {
        "name": "Black Bolt 3 Pack Blister Search",
        "url": "https://www.walmart.com/search?q=pokemon+black+bolt+3+pack+blister",
    },
    {
        "name": "Black Bolt Promo Search",
        "url": "https://www.walmart.com/search?q=pokemon+black+bolt+promo",
    },

    {
        "name": "White Flare ETB Search",
        "url": "https://www.walmart.com/search?q=pokemon+white+flare+elite+trainer+box",
    },
    {
        "name": "White Flare Booster Box Search",
        "url": "https://www.walmart.com/search?q=pokemon+white+flare+booster+box",
    },
    {
        "name": "White Flare Booster Bundle Search",
        "url": "https://www.walmart.com/search?q=pokemon+white+flare+booster+bundle",
    },
    {
        "name": "White Flare 3 Pack Blister Search",
        "url": "https://www.walmart.com/search?q=pokemon+white+flare+3+pack+blister",
    },
    {
        "name": "White Flare Promo Search",
        "url": "https://www.walmart.com/search?q=pokemon+white+flare+promo",
    },
]

LAST_STATUS = {}
LAST_ALERT_TIME = {}
DISCOVERED_URLS = set()
KNOWN_PRODUCT_URLS = {p["url"] for p in PRODUCTS}

ALERT_COOLDOWN_SECONDS = 180
DISCOVERY_ALERT_COOLDOWN_SECONDS = 900


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def send_discord(product, status, extra_lines=None):
    if not DISCORD_WEBHOOK:
        print("DISCORD_WEBHOOK missing")
        return

    lines = [
        "🚨 POKEMON ALERT",
        f"Name: {product['name']}",
        f"Status: {status}",
        f"Product: {product['url']}",
        f"Cart: {WALMART_CART_URL}",
        f"Checkout: {WALMART_CHECKOUT_URL}",
        f"Time: {now_str()}",
    ]

    if extra_lines:
        lines.extend(extra_lines)

    data = {"content": "\n".join(lines)}

    try:
        r = requests.post(DISCORD_WEBHOOK, json=data, timeout=10)
        print(f"Discord status code: {r.status_code}")
        r.raise_for_status()
    except Exception as e:
        print(f"Discord send failed: {e}")


def fetch_text(url):
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text.lower()


def fetch_raw(url):
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def classify_product_page(text):
    if "sold and shipped by walmart" in text and "add to cart" in text:
        return "in_stock_walmart"

    if "sold out" in text or "out of stock" in text:
        return "out_of_stock"

    if "more seller options" in text or "pro seller" in text or "seller reviews" in text:
        if "sold and shipped by walmart" not in text:
            return "third_party"

    if "add to cart" in text:
        return "possible_stock"

    return "unknown"


def classify_search_page(text):
    if "sold and shipped by walmart" in text and "add to cart" in text:
        return "in_stock_walmart"

    if "add to cart" in text:
        return "possible_stock"

    return "unknown"


def should_alert(url, status, cooldown=ALERT_COOLDOWN_SECONDS):
    if status not in {
        "in_stock_walmart",
        "possible_stock",
        "new_discovery",
        "discovered_stock",
    }:
        return False

    current = time.time()
    last = LAST_ALERT_TIME.get((url, status), 0)

    if current - last >= cooldown:
        LAST_ALERT_TIME[(url, status)] = current
        return True

    return False


def extract_item_id(url):
    m = re.search(r"/ip/(\d+)", url)
    return m.group(1) if m else None


def check_walmart_product_fast(product):
    item_id = extract_item_id(product["url"])
    if not item_id:
        return check_walmart_product_html(product)

    try:
        # still using the product page endpoint, but keeping structure split for future upgrades
        r = requests.get(product["url"], headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        text = r.text.lower()
        return classify_product_page(text)
    except Exception as e:
        print(f"Fast check fallback for {product['name']}: {e}")
        return check_walmart_product_html(product)


def check_walmart_product_html(product):
    try:
        text = fetch_text(product["url"])
        return classify_product_page(text)
    except Exception as e:
        print(f"Error checking {product['name']}: {e}")
        return "error"


def extract_product_links_from_search(html):
    """
    Pull likely Walmart /ip/ product links out of search result HTML.
    Keeps it simple and resilient.
    """
    links = set()

    # href="/ip/..."
    for match in re.findall(r'href="([^"]+/ip/[^"]+)"', html, flags=re.IGNORECASE):
        full = urljoin(WALMART_BASE, match.split("?")[0])
        links.add(full)

    # escaped urls sometimes appear in page source
    for match in re.findall(r'https:\\/\\/www\.walmart\.com\\/ip\\/[^"\\]+', html, flags=re.IGNORECASE):
        cleaned = match.replace("\\/", "/").split("?")[0]
        links.add(cleaned)

    return list(links)


def looks_like_target_product(url, search_name):
    """
    Light filter so discovery alerts stay relevant to Pokemon products.
    """
    lowered = url.lower()
    terms = search_name.lower()

    if "/ip/" not in lowered:
        return False

    # basic set relevance from search naming
    tokens = []
    for word in [
        "perfect", "order", "phantasmal", "flames", "destined", "rivals",
        "black", "bolt", "white", "flare", "pokemon", "elite", "trainer",
        "bundle", "booster", "promo", "blister"
    ]:
        if word in terms:
            tokens.append(word)

    if not tokens:
        return True

    hits = sum(1 for t in tokens if t in lowered)
    return hits >= 1


def discover_from_search(search):
    """
    Returns a list of newly discovered product dicts.
    """
    discoveries = []

    try:
        raw = fetch_raw(search["url"])
        links = extract_product_links_from_search(raw)

        for link in links:
            if link in KNOWN_PRODUCT_URLS or link in DISCOVERED_URLS:
                continue

            if not looks_like_target_product(link, search["name"]):
                continue

            item_id = extract_item_id(link)
            if not item_id:
                continue

            product = {
                "name": f"Discovered from {search['name']}",
                "url": link,
                "site": "product",
            }

            DISCOVERED_URLS.add(link)
            discoveries.append(product)

    except Exception as e:
        print(f"Discovery error on {search['name']}: {e}")

    return discoveries


def check_one(product):
    try:
        if product["site"] == "product":
            return check_walmart_product_fast(product)

        text = fetch_text(product["url"])
        return classify_search_page(text)

    except Exception as e:
        print(f"Error checking {product['name']}: {e}")
        return "error"


def handle_search(search):
    """
    1) classify the search page itself
    2) discover new product pages from it
    """
    status = "error"

    try:
        text = fetch_text(search["url"])
        status = classify_search_page(text)
    except Exception as e:
        print(f"Search check error for {search['name']}: {e}")

    discoveries = discover_from_search(search)
    return status, discoveries


def main():
    print("Pokemon Discovery Scanner Started")
    print("Webhook loaded:", bool(DISCORD_WEBHOOK))

    dynamic_products = []

    end_time = time.time() + 540

    while time.time() < end_time:
        # 1) Check direct known products
        for product in PRODUCTS:
            status = check_one(product)
            previous = LAST_STATUS.get(product["url"])

            print(product["name"], status)

            became_hot = (
                status in {"in_stock_walmart", "possible_stock"}
                and previous not in {"in_stock_walmart", "possible_stock"}
            )

            if became_hot and should_alert(product["url"], status):
                extra = []

                if status == "in_stock_walmart":
                    extra.append("Signal: sold and shipped by Walmart + add to cart")
                    extra.append("Best retail signal.")
                elif status == "possible_stock":
                    extra.append("Signal: add to cart text detected")
                    extra.append("Check quickly in app/browser.")

                send_discord(product, status, extra)

            LAST_STATUS[product["url"]] = status

        # 2) Check search pages + discover new product pages
        for search in SEARCHES:
            search_status, discoveries = handle_search(search)
            prev_search_status = LAST_STATUS.get(search["url"])

            print(search["name"], search_status)

            became_hot = (
                search_status in {"in_stock_walmart", "possible_stock"}
                and prev_search_status not in {"in_stock_walmart", "possible_stock"}
            )

            if became_hot and should_alert(search["url"], search_status):
                extra = ["Search page signal detected."]
                send_discord(
                    {"name": search["name"], "url": search["url"]},
                    search_status,
                    extra
                )

            LAST_STATUS[search["url"]] = search_status

            for discovered in discoveries:
                if should_alert(
                    discovered["url"],
                    "new_discovery",
                    cooldown=DISCOVERY_ALERT_COOLDOWN_SECONDS
                ):
                    send_discord(
                        discovered,
                        "new_discovery",
                        [
                            f"Found from: {search['name']}",
                            "New Walmart product page discovered.",
                            "Open it and decide if it is worth adding as a permanent direct watch.",
                        ]
                    )
                    dynamic_products.append(discovered)

        # 3) Check discovered product pages too
        for product in dynamic_products:
            status = check_one(product)
            previous = LAST_STATUS.get(product["url"])

            print(product["name"], status)

            became_hot = (
                status in {"in_stock_walmart", "possible_stock"}
                and previous not in {"in_stock_walmart", "possible_stock"}
            )

            if became_hot and should_alert(product["url"], "discovered_stock"):
                extra = [
                    "Discovered product page now looks hot.",
                    f"Detected status: {status}",
                ]
                send_discord(product, "discovered_stock", extra)

            LAST_STATUS[product["url"]] = status

        print("---- next scan ----")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
