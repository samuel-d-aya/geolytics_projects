import re
import datetime
import scrapy
from scrapy_playwright.page import PageMethod
from geopy.geocoders import Nominatim


class SuperextraSpider(scrapy.Spider):
    name = "superextra"
    allowed_domains = ["www.superxtra.com"]
    start_urls = ["https://www.superxtra.com/sucursales"]
    geolocator = Nominatim(user_agent=name)

    full_link = None

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                        PageMethod("wait_for_selector", "#Panama", timeout=60000),
                    ],
                },
                callback=self.parse,
            )

    def parse(self, response):

        stores = response.css("#Panama > div > div")

        # print(f"There are {len(stores)} on the page")

        for store in stores:

            maplink = store.css(
                ".product-item > div:nth-child(2) > div::attr(href)"
            ).get()

            full_address = store.css(
                ".product-item > div:nth-child(2) > p:nth-child(2)::text"
            ).get()
            
            #Panama > div > div:nth-child(2) > div > div.text-center.p-4 > p:nth-child(3)

            if len(maplink.split("@")) == 1:

                print(
                    f'\n\n{" ".join(store.css(".product-item > div:nth-child(2) > p::text").getall()[1:])}\n\n'
                )

                location = self.geolocator.geocode(full_address)
                lat = location.latitude
                lon = location.longitude

            else:
                full_link = maplink
                coord = full_link.split("@")[1].split(",", 2)
                lat = coord[0]
                lon = coord[1]

            print(f"\nHere is the link {maplink}\n")

            print(f"\nHere is the link {coord}\n")

            yield {
                "addr_full": full_address,
                "brand": store.css(
                    ".product-item > div:nth-child(2) > div::text"
                ).getall()[0],
                "city": store.css(
                    ".product-item > div:nth-child(2) > div::text"
                ).getall()[1],
                "country": store.css(
                    ".product-item > div:first-child > div::text"
                ).get(),
                "extras": {
                    "brand": store.css(
                        ".product-item > div:nth-child(2) > div::text"
                    ).getall()[0],
                    "fascia": store.css(
                        ".product-item > div:nth-child(2) > div::text"
                    ).getall()[0],
                    "category": "Filling Station",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Website",
                },
                "lat": lat,
                "lon": lon,
                "name": " ".join(
                    store.css(".product-item > div:nth-child(2) > div::text").getall()
                ),
                "opening_hours": self.parse_opening_hours(
                    " ".join(
                        store.css(
                            ".product-item > div:nth-child(2) > p::text"
                        ).getall()[1:]
                    )
                ),
                "phone": None,
                "postcode": None,
                "ref": f"{lat}-{lon}",
                "state": None,
                "website": None,
            }

    def parse_opening_hours(self, text):
        days_map = {
            "lunes": "Mon",
            "martes": "Tue",
            "miércoles": "Wed",
            "jueves": "Thu",
            "viernes": "Fri",
            "sábado": "Sat",
            "domingo": "Sun",
        }

        opening_hours = {}

        # Check if it's 24 hours
        if "24 horas" in text.lower():
            return {day: "24 hours" for day in days_map.values()}

        # Match patterns for Spanish day ranges and times
        patterns = [
            (
                r"Horario de lunes a sábado:\s*([\d:apm\s-]+)",
                ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
            ),
            (r"Horario de domingo:\s*([\d:apm\s-]+)", ["Sun"]),
        ]

        for pattern, days in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                time_range = match.group(1).strip()
                open_time, close_time = time_range.split(" - ")
                open_time = self.convert_to_24h(open_time)
                close_time = self.convert_to_24h(close_time)

                for day in days:
                    opening_hours[day] = f"{open_time}-{close_time}"

        return {"opening_hours": opening_hours}

    def convert_to_24h(self, time_str):

        match = re.match(r"(\d{1,2}):?(\d{0,2})?\s*(am|pm)", time_str, re.IGNORECASE)
        if match:
            hour, minute, period = match.groups()
            hour = int(hour)
            minute = minute if minute else "00"

            if period.lower() == "pm" and hour != 12:
                hour += 12
            elif period.lower() == "am" and hour == 12:
                hour = 0

            return f"{hour:02}:{minute}"

        return time_str
