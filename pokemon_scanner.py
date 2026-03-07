import time
import requests
import os
import re
from datetime import datetime

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

CHECK_INTERVAL = 10
TIMEOUT = 20

WALMART_CART_URL = "https://www.walmart.com/cart"
WALMART_CHECKOUT_URL = "https://www.walmart.com/checkout"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}

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

    {
        "name": "Perfect Order ETB Search",
        "url": "https://www.walmart.com/search?q=pokemon+perfect+order+elite+trainer+box",
        "site": "search",
    },
    {
        "name": "Perfect Order Booster Box Search",
        "url": "https://www.walmart.com/search?q=pokemon+perfect+order+booster+box",
        "site": "search",
    },
    {
        "name": "Perfect Order Booster Bundle Search",
        "url": "https://www.walmart.com/search?q=pokemon+perfect+order+booster+bundle",
        "site": "search",
    },

    {
        "name": "Phantasmal Flames ETB Search",
        "url": "https://www.walmart.com/search?q=phantasmal+flames+elite+trainer+box",
        "site": "search",
    },
    {
        "name": "Phantasmal Flames Booster Box Search",
        "url": "https://www.walmart.com/search?q=phantasmal+flames+booster+box",
        "site": "search",
    },
    {
        "name": "Phantasmal Flames Booster Bundle Search",
        "url": "https://www.walmart.com/search?q=phantasmal+flames+booster+bundle",
        "site": "search",
    },

    {
        "name": "Destined Rivals ETB Search",
        "url": "https://www.walmart.com/search?q=pokemon+destined+rivals+elite+trainer+box",
        "site": "search",
    },
    {
        "name": "Destined Rivals Booster Box Search",
        "url": "https://www.walmart.com/search?q=pokemon+destined+rivals+booster+box",
        "site": "search",
    },
    {
        "name": "Destined Rivals Booster Bundle Search",
        "url": "https://www.walmart.com/search?q=pokemon+destined+rivals+booster+bundle",
        "site": "search",
    },

    {
        "name": "Black Bolt ETB Search",
        "url": "https://www.walmart.com/search?q=pokemon+black+bolt+elite+trainer+box",
        "site": "search",
    },
    {
        "name": "Black Bolt Booster Box Search",
        "url": "https://www.walmart.com/search?q=pokemon+black+bolt+booster+box",
        "site": "search",
    },
    {
        "name": "Black Bolt Booster Bundle Search",
        "url": "https://www.walmart.com/search?q=pokemon+black+bolt+booster+bundle",
        "site": "search",
    },
    {
        "name": "Black Bolt 3 Pack Blister Search",
        "url": "https://www.walmart.com/search?q=pokemon+black+bolt+3+pack+blister",
        "site": "search",
    },
    {
        "name": "Black Bolt Promo Search",
        "url": "https://www.walmart.com/search?q=pokemon+black+bolt+promo",
        "site": "search",
    },

    {
        "name": "White Flare ETB Search",
        "url": "https://www.walmart.com/search?q=pokemon+white+flare+elite+trainer+box",
        "site": "search",
    },
    {
        "name": "White Flare Booster Box Search",
        "url": "https://www.walmart.com/search?q=pokemon+white+flare+booster+box",
        "site": "search",
    },
    {
        "name": "White Flare Booster Bundle Search",
        "url": "https://www.walmart.com/search?q=pokemon+white+flare+booster+bundle",
        "site": "search",
    },
    {
        "name": "White Flare 3 Pack Blister Search",
        "url": "https://www.walmart.com/search?q=pokemon+white+flare+3+pack+blister",
        "site": "search",
    },
    {
        "name": "White Flare Promo Search",
        "url": "https://www.walmart.com/search?q=pokemon+white+flare+promo",
        "site": "search",
    },
]

LAST_STATUS = {}
LAST_ALERT_TIME = {}
ALERT_COOLDOWN_SECONDS = 180


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


def extract_item_id(url):
    m = re.search(r"/ip/(\d+)", url)
    return m.group(1) if m else None


def check_walmart_product_fast(product):
    """
    Faster structured check for direct Walmart product pages.
    Falls back to HTML if needed.
    """
    item_id = extract_item_id(product["url"])
    if not item_id:
        return check_walmart_product_html(product)

    api_url = f"https://www.walmart.com/ip/{item_id}"

    try:
        r = requests.get(api_url, headers=HEADERS, timeout=TIMEOUT)
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
        if product["site"] == "product":
            return check_walmart_product_fast(product)

        text = fetch_text(product["url"])
        return classify_search_page(text)

    except Exception as e:
        print(f"Error checking {product['name']}: {e}")
        return "error"


def main():
    print("Pokemon Hybrid Scanner Started")
    print("Webhook loaded:", bool(DISCORD_WEBHOOK))

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
                    extra.append("Best retail signal.")
                elif status == "possible_stock":
                    extra.append("Signal: add to cart text detected")
                    extra.append("Check quickly in app/browser.")

                send_discord(product, status, extra)

            LAST_STATUS[product["url"]] = status

        print("---- next scan ----")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
