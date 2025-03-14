import json
import datetime
import scrapy


class IkeaSpider(scrapy.Spider):
    name = "ikea"
    allowed_domains = ["www.ikea.com"]
    start_urls = [
        "https://www.ikea.com/fr/fr/meta-data/informera/stores-detailed.json?cb=i30p7sowst"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
            )

    def parse(self, response):

        data = json.loads(response.text)

        for store in data:
            yield {
                "addr_full": store.get("address").get("displayAddress"),
                "brand": "Ikea",
                "city": store.get("address").get("city"),
                "country": "France",
                "extras": {
                    "brand": "Ikea",
                    "fascia": store.get("buClassification").get("name"),
                    "category": "Retail",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "website",
                },
                "lat": store.get("lat"),
                "lon": store.get("lng"),
                "name": store.get("name"),
                "opening_hours": {
                    "opening_hours": {
                        op_hr.get("day"): f'{op_hr.get("open")}-{op_hr.get("close")}'
                        for op_hr in store.get("hours").get("normal")
                    }
                },
                "phone": None,
                "postcode": store.get("address").get("zipCode"),
                "ref": store.get("id"),
                "state": store.get("address").get("stateProvinceCode"),
                "website": store.get("storePageUrl"),
            }
