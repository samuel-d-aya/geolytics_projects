import re
import json
import datetime
import scrapy
from scrapy.selector import Selector


class MymarketSpider(scrapy.Spider):
    name = "mymarket"
    allowed_domains = ["www.mymarket.gr", "maps.app.goo.gl", "www.google.com"]
    start_urls = ["https://www.mymarket.gr/stores"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,  # type: ignore
            )

    def parse(self, response):  # type: ignore

        data = json.loads(
            response.css(  # type: ignore
                "script[data-store-locator-target='storesData']::text"
            ).get()
        )
        stores = data
        for store in stores:
            more_info = Selector(text=store.get("popup"))

            self.logger.info(
                f"\n\n\n{more_info.css("div > p::text").getall() or more_info.css("div > p > span::text").getall()}\n\n\n"
            )
            yield {
                "addr_full": store.get("address"),
                "brand": "My Market",
                "city": re.sub(
                    r"\s+",
                    " ",
                    more_info.css(
                        "div > div > div:nth-child(4) > div:last-child::text"
                    ).get(),  # type: ignore
                ).split(",")[
                    -1
                ],  # type: ignore
                "country": "Greece",
                "extras": {
                    "brand": "My Market",
                    "fascia": "My Market",
                    "category": "Retail",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.get("coordinates").get("lat"),
                "lon": store.get("coordinates").get("lng"),
                "name": store.get("title"),
                "opening_hours": self.parse_opening_hours(  # type: ignore
                    more_info.css("div > p::text").getall()
                    or more_info.css("div > p > span::text").getall()
                ),
                "phone": store.get("phone"),
                "postcode": re.sub(
                    r"\s+",
                    " ",
                    more_info.css(
                        "div > div > div:nth-child(4) > div:last-child::text"
                    ).get(),  # type: ignore
                ).split(",")[
                    -2
                ],  # type: ignore
                "ref": store.get("id"),
                "state": None,
                "website": response.url,  # type: ignore
            }

    def parse_opening_hours(self, opening_hours_list):
        days_of_week_greek = {
            "Δευτέρα": "Mon",
            "Δευτ": "Mon",
            "Δευ": "Mon",
            "Τρίτη": "Tue",
            "Τρι": "Tue",
            "Τετάρτη": "Wed",
            "Τετ": "Wed",
            "Πέμπτη": "Thu",
            "Πεμ": "Thu",
            "Παρασκευή": "Fri",
            "Παρ": "Fri",
            "Σάββατο": "Sat",
            "Σαββάτο": "Sat",
            "Σαβ": "Sat",
            "Κυριακή": "Sun",
            "Κυρ": "Sun",
        }

        # Create reverse lookup for fuzzy matching
        reverse_lookup = {k: v for k, v in days_of_week_greek.items()}

        opening_hours_dict = {}

        def get_day_abbr(greek):
            for key in reverse_lookup:
                if greek.strip() in key:
                    return reverse_lookup[key]
            return None

        for item in opening_hours_list:
            if ":" not in item:
                continue

            day_part, hours_part = item.split(":", 1)
            hours = hours_part.strip().replace(".", ":").replace("-", " - ").strip()
            days = day_part.strip()

            if "-" in days:
                start_day, end_day = map(str.strip, days.split("-"))
                start_abbr = get_day_abbr(start_day)
                end_abbr = get_day_abbr(end_day)

                if start_abbr and end_abbr:
                    week_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    try:
                        start_idx = week_order.index(start_abbr)
                        end_idx = week_order.index(end_abbr)
                        for i in range(start_idx, end_idx + 1):
                            opening_hours_dict[week_order[i]] = hours
                    except ValueError:
                        continue
            else:
                day_abbr = get_day_abbr(days)
                if day_abbr:
                    opening_hours_dict[day_abbr] = hours

        return {"opening_hours": opening_hours_dict}  # type: ignore
