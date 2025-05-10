import re
import json
import datetime
import scrapy
from scrapy.selector import Selector
from scrapy_playwright.page import PageMethod


class SklavenitisSpider(scrapy.Spider):
    name = "sklavenitis"
    allowed_domains = ["www.sklavenitis.gr"]
    start_urls = ["https://www.sklavenitis.gr/about/katastimata"]

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
                callback=self.parse,
            )

    def parse(self, response):

        stores = response.css(".storeListItem")

        for store in stores:

            data = json.loads(store.css("::attr(data-store)").get())

            self.logger.info(f"\n\n{data}\n\n")

            yield {
                "addr_full": data.get("Address"),
                "brand": "Sklavenitis",
                "city": data.get("Area"),
                "country": "Greece",
                "extras": {
                    "brand": "sklavenitis",
                    "fascia": "sklavenitis",
                    "category": "Retail",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Website",
                },
                "lat": data.get("Latitude"),
                "lon": data.get("Longitude"),
                "name": f"Sklavenitis {data.get("Title")}",
                "opening_hours": self.parse_opening_hours(data.get("WorkingHours")),
                "phone": Selector(text=data.get("PhoneNumber")).css("a::text").get(),
                "postcode": data.get("ZipCode"),
                "ref": data.get("Key"),
                "state": data.get("County"),
                "website": response.url,
            }

    def parse_opening_hours(self, opening_hour):

        days_mapping = {
            "Δευτέρα": "Mon",
            "Τρίτη": "Tue",
            "Τετάρτη": "Wed",
            "Πέμπτη": "Thu",
            "Παρασκευή": "Fri",
            "Σάββατο": "Sat",
            "Κυριακή": "Sun",
        }

        day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        text = opening_hour.replace("<br/>", "\n")

        hours = {day: "Closed" for day in day_order}

        for line in text.splitlines():

            match = re.match(r"(\w+)\s*-\s*(\w+):\s*(\d{2}:\d{2}-\d{2}:\d{2})", line)
            if match:
                start_day, end_day, time_range = match.groups()
                start_idx = day_order.index(days_mapping[start_day])
                end_idx = day_order.index(days_mapping[end_day])
                for i in range(start_idx, end_idx + 1):
                    hours[day_order[i]] = time_range
                continue

            match = re.match(r"(\w+):\s*(\d{2}:\d{2}-\d{2}:\d{2})", line)
            if match:
                day, time_range = match.groups()
                eng_day = days_mapping.get(day)
                if eng_day:
                    hours[eng_day] = time_range

        return {"opening_hours": hours}
