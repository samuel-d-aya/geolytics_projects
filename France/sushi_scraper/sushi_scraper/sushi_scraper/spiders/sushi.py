import scrapy
import datetime
import json


class SushiSpider(scrapy.Spider):
    name = "sushi"
    allowed_domains = ["sushigourmet.eu"]
    start_urls = ["https://sushigourmet.eu/wp-json/hana/v2/corners"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        data = json.loads(response.text)

        for store in data:

            country = (
                store.get("acf").get("location").get("address").split(",")[-1].strip()
                if store.get("acf").get("location")
                else {}
            )

            if country == "France":
                yield {
                    "addr_full": store.get("acf").get("info").get("address"),
                    "brand": "Sushi Gourmet",
                    "city": store.get("acf").get("info").get("town"),
                    "country": country,
                    "extras": {
                        "brand": "Sushi Gourmet",
                        "fascia": store.get("acf").get("brands")[0],
                        "category": "Food & Beverages",
                        "edit_date": str(datetime.datetime.now().date()),
                        "lat_lon_source": "website",
                    },
                    "lat": store.get("acf").get("location").get("lat"),
                    "lon": store.get("acf").get("location").get("lng"),
                    "name": store.get("title"),
                    "opening_hours": self.parse_opening_hours(
                        store.get("acf").get("hours")
                    ),
                    "phone": None,
                    "postcode": store.get("acf").get("info").get("cp"),
                    "ref": store.get("ID"),
                    "state": None,
                    "website": "https://sushigourmet.eu/ou-nous-trouver/",
                }

    def parse_opening_hours(self, store):

        output = {
            "opening_hours": {
                day: f"{hour.get("opening").replace("h", ":00")}:{hour.get("closing").replace("h", ":00")}"
                for day, hour in store.items()
            }
        }
        return output
