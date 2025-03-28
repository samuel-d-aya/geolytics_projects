import scrapy
import re
import datetime
from geopy.geocoders import Nominatim


class PizzamaxSpider(scrapy.Spider):
    name = "pizzamax"
    allowed_domains = ["www.pizzamax.de"]
    start_urls = ["https://www.pizzamax.de/stores/"]
    geolocator = Nominatim(user_agent=name)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        stores = response.css(".storeContainer")

        for store in stores:

            address_output = [
                item.strip("\n").strip("\t").strip("\n").replace("/", "")
                for item in store.css(".storeAddress::text").getall()
            ]


            location = self.geolocator.geocode(f"{address_output[0]} {address_output[1]}") if self.geolocator.geocode(f"{address_output[0]} {address_output[1]}") else self.geolocator.geocode(address_output[1])

            yield {
                "addr_full": address_output[0],
                "brand": "Pizza Max",
                "city": store.css(".storeTitle::text").get(),
                "country": "Germany",
                "extras": {
                    "brand": "Pizza Max",
                    "fascia": "Pizza Max",
                    "category": "Food and Beverage",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party",
                },
                "lat": location.latitude,
                "lon": location.longitude,
                "name": f"Pizza Max {store.css(".storeTitle::text").get()}",
                "opening_hours": self.parse_opening_hours(store),
                "phone": address_output[2]
                .replace(" ", "")
                .replace("  ", "")
                .replace("Tel.:", ""),
                "postcode": address_output[1].split()[0],
                "ref": f"{float(location.latitude)}-{float(location.longitude)}",
                "state": None,
                "website": response.urljoin(store.css(".order::attr(href)").get()),
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
