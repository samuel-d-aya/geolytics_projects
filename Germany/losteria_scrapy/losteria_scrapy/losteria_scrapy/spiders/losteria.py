import re
import datetime
import scrapy
from scrapy_playwright.page import PageMethod
from geopy.geocoders import Nominatim


class LosteriaSpider(scrapy.Spider):
    name = "losteria"
    allowed_domains = ["losteria.net"]
    start_urls = [
        "https://losteria.net/en/restaurants/view/list/?tx_losteriarestaurants_restaurants%5Bfilter%5D%5Bcountry%5D=de&tx_losteriarestaurants_restaurants%5Bfilter%5D%5BsearchTerm%5D=&&&&"
    ]
    geolocator = Nominatim(user_agent=name)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                    ],
                },
                callback=self.parse_store_url,
            )

    async def parse_store_url(self, response):
        page = response.meta.get("playwright_page")

        selector = "select[name='tx_losteriarestaurants_restaurants[filter][country]']"

        try:
            await page.wait_for_selector(selector, state="attached", timeout=10000)
        except Exception as e:
            self.logger.error(f"Failed to find country selector: {str(e)}")
            return

        await page.select_option(selector, value="de", force=True)

        await page.wait_for_timeout(2000)

        parent_container = await page.query_selector("#losteria-restaurants-list")
        if not parent_container:
            return

        previous_store_count = 0
        max_scroll_attempts = 13
        scroll_attempts = 0
        last_divider_handle = None

        while scroll_attempts < max_scroll_attempts:

            dividers = await parent_container.query_selector_all(".divider")
            if not dividers:
                break

            current_last_divider = dividers[-1]
            await current_last_divider.scroll_into_view_if_needed()
            await page.wait_for_timeout(2000)

            stores = await parent_container.query_selector_all("div .text > h3 > a")
            current_store_count = len(stores)
            self.logger.info(
                f"Scroll attempt {scroll_attempts + 1}: Found {current_store_count} stores"
            )

            new_dividers = await parent_container.query_selector_all(".divider")
            new_last_divider = new_dividers[-1] if new_dividers else None

            if (
                last_divider_handle
                and new_last_divider
                and await page.evaluate(
                    "(a, b) => a === b", [last_divider_handle, new_last_divider]
                )
            ):

                break

            last_divider_handle = new_last_divider
            previous_store_count = current_store_count
            scroll_attempts += 1

        stores = await parent_container.query_selector_all("div .text > h3 > a")
        self.logger.info(f"Total stores found after scrolling: {len(stores)}")
        for store in stores:
            store_url = f"https://losteria.net{await store.get_attribute('href')}"
            yield response.follow(url=store_url, callback=self.parse)

        await page.close()

    def parse(self, response):
        self.logger.info(f"Parsing store page: {response.url}")
        full_address = re.sub(
            r"\s+", " ", response.css(".restaurant-detail .address::text").get()
        ).strip()

        location = (
            self.geolocator.geocode(full_address)
            if self.geolocator.geocode(full_address)
            else self.geolocator.geocode(full_address.split(",")[1])
        )

        yield {
            "addr_full": full_address.split(",")[0],
            "brand": "Losteria",
            "city": full_address.split(",")[1].split()[1],
            "country": "Germany",
            "extras": {
                "brand": "Losteria",
                "fascia": "Losteria",
                "category": "Food and Beverage",
                "edit_date": str(datetime.datetime.now().date()),
                "lat_lon_source": "Third Party",
            },
            "lat": location.latitude,
            "lon": location.longitude,
            "opening_hours": self.parse_opening_hours(
                response.css(".restaurant-detail >div:nth-child(3) p::text").getall()
            ),
            "phone": response.css(".restaurant-detail .contact a::text").get(),
            "postcode": full_address.split(",")[1].split()[0],
            "ref": f"{location.latitude}-{location.longitude}",
            "name": re.sub(
                r"\s+", "", response.css(".restaurant-detail .headline::text").get()
            ),
            "state": None,
            "website": response.url,
        }

    def parse_opening_hours(self, opening_hours):

        raw_text = " ".join(item.strip() for item in opening_hours if item.strip())
        cleaned_text = re.sub(r"\s+", " ", raw_text).strip()

        days_mapping = {
            "Mo.": "Mon",
            "Tu.": "Tue",
            "We.": "Wed",
            "Th.": "Thu",
            "Fr.": "Fri",
            "Sa.": "Sat",
            "Su.": "Sun",
            "Holidays": "Holiday",
        }
        opening_hours = {}

        pattern = r"([^:]+):\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})"
        matches = re.finditer(pattern, cleaned_text)

        for match in matches:
            days, open_time, close_time = match.groups()
            time_range = f"{open_time} - {close_time}"

            day_list = re.split(r"[,&]", days)
            for day in day_list:
                day = day.strip()
                if day in days_mapping:
                    opening_hours[days_mapping[day]] = time_range

        return {"opening_hours": opening_hours}
