import json
import scrapy
import datetime
import re
import calendar

class ArrowSpider(scrapy.Spider):
    name = "arrow"
    allowed_domains = ["store.united-arrows.co.jp"]
    start_urls = ["https://store.united-arrows.co.jp/stores/app/data_shops_full.json"]

    headers = {
        "Accept": "application/json; charset=utf-8 sig",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://store.united-arrows.co.jp/stores/map.html",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    }

    def start_requests(self):

        for url in self.start_urls:
            yield scrapy.Request(url=url, headers=self.headers, callback=self.parse)

    def parse(self, response):
        print(response.status)
        print(response.text[:500])

        data = json.loads(response.text)

        brand_data = data.get("brand", {})
        for store in data.get("shops", []):
            yield {
                "addr_full": store.get("address_txt"),
                "brand": brand_data.get(store.get("eBrId")).get("brandName"),
                "city": store.get("area1"),
                "country": "Japan",
                "extras": {
                    "brand": brand_data.get(store.get("eBrId")).get("brandName"),
                    "fascia": brand_data.get(store.get("eBrId")).get("brandNameKana"),
                    "category": "Fashion",
                    "edit_date": datetime.datetime.now().strftime('%Y%m%d'),
                    "lat_lon_source": "website",
                },
                "lat": store.get("point_x"),
                "lon": store.get("point_y"),
                "name": store.get("name"),
                "opening_hours": self.parse_working_hours(store.get("open_en")),
                "phone": re.findall(
                    r"\b\d{2,3}-\d{2,5}-\d{2,5}\b", store.get("phone_en")
                ),
                "postcode": store.get("address_num"),
                "ref": store.get("shopnum"),
                "state": store.get("area2"),
                "website": store.get("url1"),
            }

    def parse_working_hours(self, opening_hours):

        if re.match(
            r"^\d{2}:\d{2}-\d{2}:\d{2}$|^\d{2}:\d{2}~\d{2}:\d{2}$", opening_hours
        ):
            return {
            "opening_hours": {
                "Mon": opening_hours,
                "Tue": opening_hours,
                "Wed": opening_hours,
                "Thur": opening_hours,
                "Fri": opening_hours,
                "Sat": opening_hours,
                "Sun": opening_hours,
            }
        }
            
        return {opening_hours}
