import json
import datetime
import scrapy


class VansSpider(scrapy.Spider):
    name = "vans"
    allowed_domains = ["www.vans.co.kr"]
    start_urls = ["https://www.vans.co.kr/store?isPaging=false"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        output = response.css(
            "#wrapper > main > article > div.store-content-container > div::attr(data-store-list)"
        ).get()

        data = json.loads(output)

        for store in data:
            yield {
                "addr_full": f"{store.get("address1")} {store.get("address2")}",
                "brand": "Vans",
                "city": store.get("city"),
                "country": "South Korea",
                "extras": {
                    "brand": "Vans",
                    "fascia": "Vans",
                    "category": "Retail",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
                "name": store.get("name"),
                "opening_hours": {
                    "opening_hours": {
                        "Mon": " ",
                        "Tue": " ",
                        "Wed": " ",
                        "Thu": " ",
                        "Fri": " ",
                        "Sat": " ",
                        "Sun": " ",
                    }
                },
                "phone": store.get("phone"),
                "postcode": store.get("zip"),
                "ref": store.get("id"),
                "state": store.get("state"),
                "website": "https://www.vans.co.kr/store?isPaging=false",
            }
