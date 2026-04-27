import re
import time
import random
from playwright.sync_api import sync_playwright

running = False
visited_domains = set()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

BASE_URL = "https://www.tokopedia.com/p/{}/{}/?page={}&fcity={}"


def slugify(text):
    text = text.lower().replace("&", "-")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")


def stop_scraper():
    global running
    running = False


def scroll_page(page):
    last = 0
    while running:
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(1000)
        new = page.evaluate("document.body.scrollHeight")
        if new == last:
            break
        last = new


def get_shop_info(context, domain):
    try:
        r = context.request.post(
            "https://gql.tokopedia.com/graphql/ShopInfoCore",
            data=[{
                "operationName": "ShopInfoCore",
                "variables": {"id": 0, "domain": domain},
                "query": """
query ShopInfoCore($id: Int!, $domain: String) {
  shopInfoByID(input:{
    shopIDs:[$id]
    fields:["core","create_info","location","other-shiploc","active_product"]
    domain:$domain
    source:"shoppage"
  }){
    result{
      shopCore{ domain name }
      createInfo{ openSince }
      activeProduct
      shippingLoc{ districtName cityName }
    }
  }
}
"""
            }]
        )

        data = r.json()
        shop = data[0]["data"]["shopInfoByID"]["result"][0]

        return {
            "domain": shop["shopCore"]["domain"],
            "shop_name": shop["shopCore"]["name"],
            "city": shop["shippingLoc"]["cityName"],
            "district": shop["shippingLoc"]["districtName"],
            "open_since": shop["createInfo"]["openSince"],
            "active_product": shop["activeProduct"],
        }

    except:
        return None


def run_scraper(update_callback, city_code, categories, max_page, on_finish):
    global running, visited_domains

    running = True
    visited_domains = set()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS)
            )

            for base_cat, subs in categories.items():
                for sub in subs:

                    if not running:
                        break

                    slug = slugify(sub)
                    page_num = 1

                    while running and page_num <= max_page:

                        url = BASE_URL.format(base_cat, slug, page_num, city_code)
                        print("OPEN:", url)

                        page = context.new_page()

                        try:
                            page.goto(url, timeout=60000)
                            page.wait_for_timeout(3000)
                        except:
                            page.close()
                            break

                        scroll_page(page)

                        products = page.query_selector_all('[data-testid="lnkProductContainer"]')

                        if not products:
                            page.close()
                            break

                        for pdt in products:
                            link = pdt.get_attribute("href")
                            if not link:
                                continue

                            match = re.search(r"tokopedia.com/([^/]+)/", link)
                            if not match:
                                continue

                            domain = match.group(1)

                            if domain in visited_domains:
                                continue

                            visited_domains.add(domain)

                            data = get_shop_info(context, domain)

                            if data:
                                update_callback(data)

                            time.sleep(0.2)

                        page.close()
                        page_num += 1

            browser.close()

    finally:
        running = False
        on_finish()