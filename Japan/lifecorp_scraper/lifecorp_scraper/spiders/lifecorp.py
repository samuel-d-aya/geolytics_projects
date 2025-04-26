import json
import datetime
import re
import scrapy


class LifecorpSpider(scrapy.Spider):
    name = "lifecorp"
    allowed_domains = ["g9ey9rioe.api.hp.can-ly.com"]
    start_urls = ["https://g9ey9rioe.api.hp.can-ly.com/v2/companies/1077/shops/search"]

    headers = {
        "Accept": "application/json; charset=utf-8-sig",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://store.lifecorp.jp/map/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    }

    def start_requests(self):
        for endpoint in self.start_urls:
            yield scrapy.Request(
                url=endpoint, headers=self.headers, callback=self.parse
            )

    def parse(self, response):
        data = json.loads(response.text)

        for store in data.get("shops", []):
            yield {
                "addr_full": store.get("address"),
                "brand": "Lifecorp",
                "city": store.get("area1"),
                "country": "Japan",
                "extras": {
                    "brand": "Lifecorp",
                    "fascia": "Lifecorp",
                    "category": "Store",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "website",
                },
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
                "name": store.get("nameKana"),
                "opening_hours": self.parse_working_hours(store.get("businessHours")),
                "phone": store.get("phoneNumber"),
                "postcode": store.get("postalCode"),
                "ref": store.get("storeId"),
                "state": None,
                "website": "https://store.lifecorp.jp/",
            }

    def parse_working_hours(self, opening_hours):

        days_mapping = {
            "SUNDAY": "Sun",
            "MONDAY": "Mon",
            "TUESDAY": "Tue",
            "WEDNESDAY": "Wed",
            "THURSDAY": "Thur",
            "FRIDAY": "Fri",
            "SATURDAY": "Sat",
        }
        opening_hour = {}

        for weekday in opening_hours:
            opening_hour[days_mapping.get(weekday.get("name"))] = (
                f"{weekday.get("openTime")}-{weekday.get("closeTime")}"
            )

        return {"opening_hour": opening_hour}
