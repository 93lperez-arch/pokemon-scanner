import time
import requests
import os
from datetime import datetime

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

CHECK_INTERVAL = 15
TIMEOUT = 20

WALMART_CART_URL = "https://www.walmart.com/cart"
WALMART_CHECKOUT_URL = "https://www.walmart.com/checkout"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}

PRODUCTS = [

    # ===== DIRECT PRODUCT PAGES =====

    {
        "name": "Prismatic Evolutions ETB",
        "url": "https://www.walmart.com/ip/13816151308",
        "site": "product"
    },
    {
        "name": "Prismatic Evolutions Booster Bundle",
        "url": "https://www.walmart.com/ip/5373472869",
        "site": "product"
    },
    {
        "name": "Pokemon 151 Booster Bundle",
        "url": "https://www.walmart.com/ip/1160437186",
        "site": "product"
    },
    {
        "name": "Surging Sparks ETB",
        "url": "https://www.walmart.com/ip/10692607747",
        "site": "product"
    },

    # ===== SEARCH PAGES =====

    {
        "name": "Perfect Order ETB Search",
        "url": "https://www.walmart.com/search?q=pokemon+perfect+order+elite+trainer+box",
        "site": "search"
    },
    {
        "name": "Perfect Order Booster Box Search",
        "url": "https://www.walmart.com/search?q=pokemon+perfect+order+booster+box",
        "site": "search"
    },
    {
        "name": "Perfect Order Booster Bundle Search",
        "url": "https://www.walmart.com/search?q=pokemon+perfect+order+booster+bundle",
        "site": "search"
    },
    {
        "name": "Phantasmal Flames ETB Search",
        "url": "https://www.walmart.com/search?q=phantasmal+flames+elite+trainer+box",
        "site": "search"
    },
    {
        "name": "Phantasmal Flames Booster Box Search",
        "url": "https://www.walmart.com/search?q=phantasmal+flames+booster+box",
        "site": "search"
    },
    {
        "name": "Phantasmal Flames Booster Bundle Search",
        "url": "https://www.walmart.com/search?q=phantasmal+flames+booster+bundle",
        "site": "search"
    },
    {
        "name": "Destined Rivals ETB Search",
        "url": "https://www.walmart.com/search?q=pokemon+destined+rivals+elite+trainer+box",
        "site": "search"
    },
    {
        "name": "Destined Rivals Booster Box Search",
        "url": "https://www.walmart.com/search?q=pokemon+destined+rivals+booster+box",
        "site": "search"
    },
    {
        "name": "Destined Rivals Booster Bundle Search",
        "url": "https://www.walmart.com/search?q=pokemon+destined+rivals+booster+bundle",
        "site": "search"
    }
]

LAST_STATUS = {}
LAST_ALERT_TIME = {}

ALERT_COOLDOWN_SECONDS = 180


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def send_discord(product, status, extra_lines=None):

    if not DISCORD_WEBHOOK:
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
        requests.post(DISCORD_WEBHOOK, json=data, timeout=10)
    except:
        pass


def fetch_text(url):

    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()

    return r.text.lower()


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


def should_alert(url, status):

    if status not in {"in_stock_walmart", "possible_stock"}:
        return False

    current = time.time()

    last = LAST_ALERT_TIME.get(url, 0)

    if current - last >= ALERT_COOLDOWN_SECONDS:
        LAST_ALERT_TIME[url] = current
        return True

    return False


def check_one(product):

    try:

        text = fetch_text(product["url"])

        if product["site"] == "product":
            status = classify_product_page(text)
        else:
            status = classify_search_page(text)

        return status

    except Exception:
        return "error"


def main():

    print("Pokemon Hybrid Scanner Started")

    end_time = time.time() + 540

    while time.time() < end_time:

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

                elif status == "possible_stock":
                    extra.append("Signal: add to cart text detected")

                send_discord(product, status, extra)

            LAST_STATUS[product["url"]] = status

        print("---- next scan ----")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
