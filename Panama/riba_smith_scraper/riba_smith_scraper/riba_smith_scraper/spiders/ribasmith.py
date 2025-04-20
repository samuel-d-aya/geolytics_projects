import re
import datetime
import scrapy
from scrapy_playwright.page import PageMethod
import requests
import logging


class RibasmithSpider(scrapy.Spider):
    name = "ribasmith"
    start_urls = ["https://www.ribasmith.com/index.php/tiendasrs"]
    
    custom_settings = {
        'DOWNLOAD_TIMEOUT': 60,           # Increase general timeout to 60 seconds
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'timeout': 60000,             # Browser launch timeout (60 seconds)
            'headless': False,            # Set to False to see what's happening
        },
        'PLAYWRIGHT_BROWSER_TYPE': 'firefox',  # Try Firefox instead of Chromium
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000,  # Navigation timeout (60 seconds)
        'CONCURRENT_REQUESTS': 1,         # Process one request at a time
        'RETRY_TIMES': 3,                 # Number of retries
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 404, 403, 429],  # Codes to retry
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),  # Less strict waiting
                    ],
                    "playwright_context_kwargs": {
                        "viewport": {"width": 1920, "height": 1080},
                        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    },
                },
                callback=self.extract_store_links,
                errback=self.errback_handler,
            )

    async def extract_store_links(self, response):
        page = response.meta["playwright_page"]
        
        try:
            # Wait for page to load properly
            await page.wait_for_selector('#mw-all-stores', timeout=30000)
            
            # Get store elements
            store_elements = await page.query_selector_all('#mw-all-stores div > ul > li')
            self.logger.info(f"Found {len(store_elements)} store elements")
            
            # Extract links manually for more control
            store_urls = []
            
            for i, store in enumerate(store_elements):
                try:
                    self.logger.info(f"Processing store element {i+1}")
                    
                    # Click to expand store details
                    detail_btn = await store.query_selector('.mw-sl__stores__list__item__right > div:nth-child(2)')
                    if not detail_btn:
                        self.logger.warning(f"No detail button found for store {i+1}")
                        continue
                        
                    await detail_btn.click()
                    await page.wait_for_timeout(3000)  # Wait longer between interactions
                    
                    # Try to find store URL with multiple selectors
                    url = None
                    for selector in [
                        'div:nth-child(2) > div > ul > li:nth-child(1) > a',
                        'div.mw-sl__stores__list__item__details a',
                        '.mw-sl__stores__list__item__details a'
                    ]:
                        detail_link = await store.query_selector(selector)
                        if detail_link:
                            url = await detail_link.get_attribute('href')
                            if url:
                                self.logger.info(f"Found URL for store {i+1}: {url}")
                                store_urls.append(url)
                                break
                    
                    if not url:
                        self.logger.warning(f"Could not find URL for store {i+1}")
                        
                    # Take screenshot for debugging
                    await page.screenshot(path=f"debug_store_{i+1}.png")
                    
                except Exception as e:
                    self.logger.error(f"Error processing store element {i+1}: {str(e)}")
            
            self.logger.info(f"Total store URLs found: {len(store_urls)}")
            await page.close()
            
            # Save URLs to file as a backup
            with open('store_urls.txt', 'w') as f:
                for url in store_urls:
                    f.write(f"{url}\n")
            
            # Process each store URL
            for url in store_urls:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_store_details,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_load_state", "domcontentloaded"),
                        ],
                        "playwright_context_kwargs": {
                            "viewport": {"width": 1920, "height": 1080},
                            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        },
                    },
                    errback=self.errback_handler,
                    dont_filter=True,  # In case of URL duplication
                )
                
        except Exception as e:
            self.logger.error(f"Error in extract_store_links: {str(e)}")
            await page.close()

    async def parse_store_details(self, response):
        page = response.meta["playwright_page"]
        
        try:
            # Save screenshot for debugging
            await page.screenshot(path=f"store_detail_{response.url.split('/')[-1]}.png")
            
            # Wait for store details with shorter timeout
            try:
                await page.wait_for_selector(".mw-sl__details", timeout=15000)
            except Exception as e:
                self.logger.warning(f"Timeout waiting for store details selector: {str(e)}")
                
            # Get content even if selector timeout occurred
            content = await page.content()
            html_response = response.replace(body=content)
            
            store = html_response.css(".mw-sl__details")
            
            if not store:
                self.logger.warning(f"Store details not found on page: {response.url}")
                await page.close()
                return

            # Get map link for geocoding
            maplink_raw = store.css(".mw-sl__details__item--direction > a::attr(href)").get()
            if not maplink_raw:
                self.logger.warning(f"Map link not found on store details page: {response.url}")
                await page.close()
                return

            maplink = f"https:{maplink_raw}" if not maplink_raw.startswith("http") else maplink_raw

            # Get coordinates
            try:
                search_addr = maplink.split("location&daddr=")[1] if "location&daddr=" in maplink else ""
                if not search_addr:
                    self.logger.warning(f"Could not extract address from map link: {maplink}")
                    # Use default coordinates as fallback
                    result = [0, 0]
                else:
                    output = requests.get(f"https://photon.komoot.io/api/?q={search_addr}", timeout=10)
                    result = output.json()["features"][0]["geometry"]["coordinates"]
            except Exception as e:
                self.logger.error(f"Geocoding failed for map link: {maplink} | Error: {str(e)}")
                # Use default coordinates as fallback
                result = [0, 0]

            # Extract store name and other details
            store_name = html_response.css(".mw-sl__details > h2::text").get() or "Unknown Store"
            
            # Extract city
            city = None
            if store_name and " Smith " in store_name:
                city = store_name.split(" Smith ")[1]
            else:
                self.logger.warning(f"Could not parse city from store name: {store_name}")

            # Get address
            addr_texts = store.css(".mw-sl__details__item--location::text").getall()
            addr_full = re.sub(r"\s+", " ", " ".join(addr_texts)).strip() if addr_texts else "Address not available"

            # Create store data
            store_data = {
                "addr_full": addr_full,
                "brand": "Riba Smith",
                "city": city,
                "country": "Panama",
                "extras": {
                    "brand": "Riba Smith",
                    "fascia": "Riba Smith",
                    "category": "Supermarket",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party",
                },
                "lat": result[1] if len(result) > 1 else 0,
                "lon": result[0] if len(result) > 0 else 0,
                "name": store_name,
                "opening_hours": self.parse_opening_hours(
                    html_response.css(".mw-sl__infotable__table > tbody > tr")
                ),
                "phone": None,
                "postcode": None,
                "ref": f"{result[1]}-{result[0]}" if len(result) > 1 else "unknown",
                "state": None,
                "website": response.url,
            }
            
            yield store_data
            
        except Exception as e:
            self.logger.error(f"Error processing store details for {response.url}: {str(e)}")
        finally:
            if page:
                await page.close()

    def errback_handler(self, failure):
        """Handle request failures"""
        # Extract the request
        request = failure.request
        self.logger.error(f"Request failed: {request.url}")
        self.logger.error(f"Error: {failure.value}")
        
        # If there was a Playwright page involved, make sure to close it
        if 'playwright_page' in request.meta:
            page = request.meta['playwright_page']
            # We need to use try/except here because we might be in a different execution context
            try:
                import asyncio
                asyncio.ensure_future(page.close())
            except Exception as e:
                self.logger.error(f"Failed to close page: {e}")

    def parse_opening_hours(self, opening_hours):
        days_map = {
            "Monday": "Mon",
            "Tuesday": "Tue",
            "Wednesday": "Wed",
            "Thursday": "Thu",
            "Friday": "Fri",
            "Saturday": "Sat",
            "Sunday": "Sun",
        }

        opening_hours_dict = {}
        for day in opening_hours:
            day_name = day.css("tr > td:nth-child(1)::text").get()
            hours = day.css("tr > td:nth-child(2) > span::text").get()

            if day_name and hours:
                hours = re.sub(r"\s+", " ", hours).strip()
                opening_hours_dict[day_name] = hours

        return {
            "opening_hours": {
                days_map[day]: hours for day, hours in opening_hours_dict.items()
                if day in days_map
            }
        }