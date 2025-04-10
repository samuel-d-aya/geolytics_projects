import re
import datetime
import scrapy
from geopy.geocoders import Nominatim


class AvantiSpider(scrapy.Spider):
    name = "avanti"
    allowed_domains = ["www.avanti.de"]
    start_urls = ["https://www.avanti.de/bestellen/"]
    geolocator = Nominatim(user_agent=name)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        stores = response.css("store-box")

        for store in stores:

            address_output = [
                re.sub(r"\s+", " ", item).strip()
                for item in store.css("store-address::text").getall()
            ]

            location = self.geolocator.geocode(f"{address_output[1]} {address_output[2]}")

            yield {
                "addr_full": address_output[1],
                "city": re.sub(r"\s+", "", store.css("store-title::text").get()),
                "country": "Germany",
                "brand": "Pizza Avanti",
                "extras": {
                    "brand": "Pizza Avanti",
                    "fascia": "Pizza Avanti",
                    "category": "Food and Beverage",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party",
                },
                "lat": location.latitude,
                "lon": location.longitude,
                "opening_hours": self.parse_opening_hours(store),
                "phone": None,
                "ref": f"{float(location.latitude)}-{float(location.longitude)}",
                "postcode": address_output[2].split()[0],
                "name": f"Avanti {re.sub(r"\s+", "", store.css("store-title::text").get())}",
                "state": None,
                "website": response.urljoin(
                    store.css("store-buttons a::attr(href)").get()
                ),
            }

    def parse_opening_hours(self, store):

        output = {}

        table_heads = store.css("table th::text").getall()
        table_data = store.css("table td::text").getall()

        hours_list = [item for item in table_data if item.find("Uhr") > 0]
        hour_day = [thd[0 : len(tdd) + 1] for thd, tdd in zip(table_heads, hours_list)]

        for iday, jhour in zip(hour_day, hours_list):
            output[iday] = jhour

        parsed_hours = {}
        for days, time_range in output.items():
            time_range = time_range.replace(" Uhr", "")
            for day in self.expand_days(days):
                parsed_hours[day] = time_range

        return {"opening_hours": parsed_hours}

    def expand_days(self, days):
        days_mapping = {
            "Mo": "Mon",
            "Di": "Tue",
            "Mi": "Wed",
            "Do": "Thur",
            "Fr": "Fri",
            "Sa": "Sat",
            "So": "Sun",
            "Feiertage": "Holiday",
        }

        expanded = []
        parts = re.split(r",|\s+", days)
        for part in parts:
            match = re.match(r"([A-Za-z]+)-([A-Za-z]+)", part)
            if match:
                start, end = match.groups()
                keys = list(days_mapping.keys())
                if start in keys and end in keys:
                    expanded.extend(keys[keys.index(start) : keys.index(end) + 1])
            elif part in days_mapping:
                expanded.append(part)
        return [days_mapping[d] for d in expanded if d in days_mapping]
