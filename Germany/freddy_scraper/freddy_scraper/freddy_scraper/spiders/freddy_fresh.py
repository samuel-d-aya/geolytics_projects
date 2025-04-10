import datetime
import re
import scrapy
from geopy.geocoders import Nominatim


class FreddyFreshSpider(scrapy.Spider):
    name = "freddy_fresh"
    allowed_domains = ["www.freddy-fresh.de"]
    start_urls = ["https://www.freddy-fresh.de/stores/"]
    geolocator = Nominatim(user_agent=name)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        stores = response.css(".store")

        for store in stores:

            address_output = [
                re.sub(r"\s+", " ", item).strip()
                for item in store.css(".address::text").getall()
            ]

            location = self.geolocator.geocode(f"{address_output[0]} {address_output[1]}") if self.geolocator.geocode(f"{address_output[0]} {address_output[1]}") else self.geolocator.geocode(address_output[1])

            yield {
                "addr_full": address_output[0],
                "brand": "Freddy Fresh",
                "city": address_output[1].split()[1],
                "country": "Germany",
                "extras": {
                    "brand": "Freddy Fresh",
                    "fascia": "Freddy Fresh",
                    "category": "Food and Beverage",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party",
                },
                "lat": location.latitude,
                "lon": location.longitude,
                "opening_hours": self.parse_opening_hours(store),
                "phone": re.sub(r"\s+", "", store.css(".phone a::text").getall()[1]),
                "postcode": address_output[1].split()[0],
                "ref": f"{float(location.latitude)}-{float(location.longitude)}",
                "name": store.css(".title a::text").get(),
                "state": None,
                "website": response.urljoin(response.css(".title a::attr(href)").get()),
            }

    def parse_opening_hours(self, store):

        output = {}
        days_mapping = {
            "Montag": "Mon",
            "Dienstag": "Tue",
            "Mittwoch": "Wed",
            "Donnerstag": "Thu",
            "Freitag": "Fri",
            "Samstag": "Sat",
            "Sonntag": "Sun",
            "Feiertag": "Holiday",
            "Feiertage": "Holiday",
        }

        table_heads = store.css("table th::text").getall()
        table_data = store.css("table td::text").getall()

        hours_list = [item for item in table_data if item.find("Uhr") > 0]
        hour_day = [thd[0 : len(tdd) + 1] for thd, tdd in zip(table_heads, hours_list)]

        for iday, jhour in zip(hour_day, hours_list):
            output[iday] = jhour

            parsed_hour = {}
        for day, time in output.items():
            shortend_ver = days_mapping.get(day.replace(":", ""), day)
            parsed_hour[shortend_ver] = time.replace("Uhr", "")

        return {"opening_hours": parsed_hour}
