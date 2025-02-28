import json
import random
import datetime
import scrapy
import calendar
from scrapy_playwright.page import PageMethod
from playwright_stealth import stealth_async
from scrapy.selector import Selector


class BrunellSpider(scrapy.Spider):
    name = "brunell"
    allowed_domains = ["shop.brunellocucinelli.com"]
    start_urls = [
        "https://shop.brunellocucinelli.com/on/demandware.store/Sites-bc-us-Site/en_US/Stores-findBoutiques"
    ]

    params = {"countryCode": "JP"}

    def start_requests(self):

        url = f"{self.start_urls[0]}?countryCode={self.params['countryCode']}"
        self.logger.info(f"Requesting URL: {url}")

        yield scrapy.Request(
            url=url,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "networkidle"),
                    PageMethod("wait_for_selector", "body", timeout=60000),
                ],
            },
            callback=self.parse,
            errback=self.errback,
        )

    async def parse(self, response):
        page = response.meta.get("playwright_page")
        if page:
            await stealth_async(page)
            try:
                await page.evaluate("window.scrollBy(0, Math.random() * 500 + 200)")
                await page.wait_for_timeout(random.randint(2000, 5000))

                content = await page.content()
                self.logger.debug(f"Page content snippet: {content[:500]}")

                selector = Selector(text=content)
                pre_text = selector.xpath("//pre/text()").get()
                if not pre_text:
                    self.logger.error("No <pre> tag found in response")
                    return

                try:
                    data = json.loads(pre_text.strip())
                    self.logger.info(
                        f"Parsed JSON from <pre>: {json.dumps(data, indent=2)[:500]}"
                    )
                except json.JSONDecodeError as e:
                    self.logger.error(
                        f"Failed to parse JSON from <pre>: {pre_text[:500]} - Error: {str(e)}"
                    )
                    return
            except Exception as e:
                self.logger.error(f"Playwright error: {str(e)}")
            finally:
                await page.close()

        if not data.get("filterList"):
            self.logger.warning("No stores found in filterList")
            return

        for store in data.get("filterList", []):
            try:

                hours_raw = store.get("storeHours", "").replace("<br>", "").strip()
                opening_hours = {}
                if "Monday-Sunday" in hours_raw:
                    times = hours_raw.split(":", 1)[1].strip() if ":" in hours_raw else ""
                    # Create entry for each day with the same hours
                    for i in range(7):
                        opening_hours[calendar.day_name[i][:3]] = times

                yield {
                    "addr_full": store.get("address1", ""),
                    "brand": "brunellocucinelli",
                    "city": store.get("city", ""),
                    "country": store.get("country", ""),
                    "extras": {
                        "brand": "brunellocucinelli",
                        "fascia": "brunellocucinelli",
                        "category": "Fashion",
                        "edit_date": datetime.datetime.now().strftime('%Y%m%d'),
                        "lat_lon_source": "website",
                    },
                    "lat": store.get("markers", {}).get("lat", ""),
                    "long": store.get("markers", {}).get("long", ""),
                    "name": store.get("name", ""),
                    "opening_hours": opening_hours,
                    "phone": store.get("phone", ""),
                    "postcode": store.get("postalCode", ""),
                    "ref": store.get("ID", ""),
                    "state": "",
                    "website": store.get("url", ""),
                }
            except Exception as e:
                self.logger.error(
                    f"Error processing store {store.get('name', 'Unknown')}: {str(e)}"
                )

    async def errback(self, failure):
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
        self.logger.error(f"Request failed: {repr(failure)}")
        yield {"url": failure.request.url, "error": str(failure)}
