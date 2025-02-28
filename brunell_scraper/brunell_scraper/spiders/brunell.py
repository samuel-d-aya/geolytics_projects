import json
import random
import datetime
import scrapy
from googletrans import Translator
import time
from scrapy_playwright.page import PageMethod
from playwright_stealth import stealth_async
from scrapy.selector import Selector


class BrunellSpider(scrapy.Spider):
    name = "brunell"
    allowed_domains = ["shop.brunellocucinelli.com"]
    start_urls = [
        "https://shop.brunellocucinelli.com/on/demandware.store/Sites-bc-us-Site/en_US/Stores-findBoutiques"
    ]
    translator = Translator()

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
        
    def translate_text(self, text, retries=3):
        """Translate text with retry mechanism"""
        if not text or not text.strip():
            return ""
            
        for attempt in range(retries):
            try:
                # Delay to avoid hitting rate limits
                time.sleep(1)
                result = self.translator.translate(text, src='ja', dest='en')
                return result.text
            except Exception as e:
                if attempt == retries - 1:  # Last attempt
                    self.logger.error(f"Translation failed for text '{text}': {str(e)}")
                    return text  # Return original text if translation fails
                time.sleep(2)  # Wait before retrying
        return text
    
    def translate_store_data(self, store):
        """Translate store data fields"""
        try:
            address_en = self.translate_text(store.get("address1", ""))
            hours_raw = store.get("storeHours", "").replace("<br>", "").strip()
            opening_hours = {}
            if hours_raw and ":" in hours_raw:
                days, times = hours_raw.split(":", 1)
                opening_hours[days.strip()] = times.strip()
            
            return {
                    "addr_full": address_en,
                    "brand": "brunellocucinelli",
                    "city": store.get("city", ""),
                    "country": store.get("country", ""),
                    "extras": {
                        "brand": "brunellocucinelli",
                        "fascia": "",
                        "category": "",
                        "edit_date": datetime.datetime.now().isoformat(),
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
            self.logger.error(f"Translation error: {str(e)}")
            # Return data without translation if translation fails
            return {
                    "addr_full": store.get("address1", ""),
                    "brand": "brunellocucinelli",
                    "city": store.get("city", ""),
                    "country": store.get("country", ""),
                    "extras": {
                        "brand": "brunellocucinelli",
                        "fascia": "",
                        "category": "",
                        "edit_date": datetime.datetime.now().isoformat(),
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
            store_item = self.translate_store_data(store)

            yield store_item

    async def errback(self, failure):
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
        self.logger.error(f"Request failed: {repr(failure)}")
        yield {"url": failure.request.url, "error": str(failure)}
