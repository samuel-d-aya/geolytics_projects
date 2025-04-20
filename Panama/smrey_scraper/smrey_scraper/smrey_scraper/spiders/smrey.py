import re
import datetime
import scrapy
from scrapy_playwright.page import PageMethod
from geopy.geocoders import Nominatim
import requests


class SmreySpider(scrapy.Spider):
    name = "smrey"
    # allowed_domains = ["www.smrey.com"]
    start_urls = ["https://www.smrey.com/Sucursales"]

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
                        PageMethod(
                            "wait_for_selector",
                            "#home-wrapper__container",
                            timeout=60000,
                        ),
                    ],
                },
                callback=self.parse_store_url,
            )

    async def parse_store_url(self, response):
        page = response.meta.get("playwright_page")

        self.logger.info(
            f'\n\nParsing store page: {response.css("#home-wrapper__container > div > div > div > div > select > option").getall()}\n\n'
        )

        selector = "#home-wrapper__container > div > div > div > div > select > option"
        all_options = await page.query_selector_all(selector)
        options = all_options[1:]

        for option in options:
            value = await option.get_attribute("value")

            await page.select_option(
                "#home-wrapper__container > div > div > div > div > select",
                value=value,
                force=True,
            )
            await page.wait_for_timeout(2000)
            full_html = await page.content()
            # await page.close()
            new_response = response.replace(body=full_html, encoding="utf-8")
            stores = new_response.css(
                "#home-wrapper__container > div > div > div > div > div > div"
            )
            print(f"\n\nThere are {len(stores)} on the page\n\n")

            for store in stores:

                store_name = store.css("h3::text").get()
                store_address = store.css("p:nth-child(3)::text").get()
                store_phone = store.css("p:nth-child(2)::text").get()
                store_opening = store.css("p:nth-child(4)::text").get()
                maplink = store.css("a::attr(href)").get()
                print(f"\n\n{maplink}\n\n")
                print(f"\n\nstore name: {store_name}\n\n")

                search_addr = (
                    f"Supermercados Rey | {store_name.replace("Rey ", "")} | Panama"
                )
                output = requests.get(f"https://photon.komoot.io/api/?q={search_addr}")
                result = output.json()["features"][0]["geometry"]["coordinates"]

                yield {
                    "addr_full": store_address.split(":")[1],
                    "brand": "Rey",
                    "city": value,
                    "country": "Panama",
                    "extras": {
                        "brand": "Rey",
                        "fascia": "Rey",
                        "category": "Supermarket",
                        "edit_date": str(datetime.datetime.now().date()),
                        "lat_lon_source": "Third Party",
                    },
                    "lat": result[1],
                    "lon": result[0],
                    "name": store_name,
                    "opening_hours": self.parse_opening_hours(store_opening),
                    "phone": store_phone.split(":")[1],
                    "ref": f"{result[1]}-{result[0]}",
                    "postcode": None,
                    "state": None,
                    "website": new_response.url,
                }

                # yield new_response.follow(
                #     url=maplink,
                #     meta=meta,
                #     callback=self.parse_maplink,
                # )

    # def parse_maplink(self, response):
    #     maplink = response.url

    #     latitude = re.search(r"@(-?\d+\.\d+),", maplink).group(1)
    #     longitude = re.search(r"(-?\d+\.\d+)z", maplink).group(1)
    #     yield {
    #         "addr_full": response.meta["addr_full"],
    #         "brand": response.meta["brand"],
    #         "city": response.meta["city"],
    #         "country": response.meta["country"],
    #         "extras": response.meta["extras"],
    #         "lat": latitude,
    #         "lon": longitude,
    #         "name": response.meta["name"],
    #         "opening_hours": response.meta["opening_hours"],
    #         "phone": response.meta["phone"],
    #         "postcode": response.meta["postcode"],
    #         "ref": f"{latitude}-{longitude}",
    #         "state": response.meta["state"],
    #         "website": response.meta["website"],
    #     }

    def parse_opening_hours(self, text):

        days_order = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

        text = text.strip()

        time_match = re.search(
            r"(\d{1,2}:\d{2})\s*(am|pm)\s*a\s*(\d{1,2}:\d{2})\s*(am|pm)",
            text,
            re.IGNORECASE,
        )
        if not time_match:
            return {}

        open_time = f"{time_match[1]}".strip()
        close_time = f"{time_match[3]}".strip()

        days_match = re.search(r"(Lun)\s*a\s*(Dom)", text)
        if not days_match:
            return {}

        start_day, end_day = days_match.groups()

        start_idx = days_order.index(start_day)
        end_idx = days_order.index(end_day) + 1

        applicable_days = days_order[start_idx:end_idx]

        opening_hours = {day: f"{open_time} - {close_time}" for day in applicable_days}

        return {"opening_hours": opening_hours}
