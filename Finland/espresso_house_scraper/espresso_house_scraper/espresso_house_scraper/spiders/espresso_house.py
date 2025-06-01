import json
import datetime
from typing import Iterable, Dict, Any, List
import scrapy
from scrapy.http.request import Request
from scrapy.http.response import Response


class EspressoHouseSpider(scrapy.Spider):
    name = "espresso_house"
    allowed_domains = ["myespressohouse.com"]
    start_urls = ["https://myespressohouse.com/beproud/api/CoffeeShop/v2"]

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Origin": "https://fi.espressohouse.com",
        "Pragma": "no-cache",
        "Referer": "https://fi.espressohouse.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield scrapy.Request(url=url, headers=self.headers, callback=self.parse)

    def parse(self, response: Response) -> Iterable[Dict[str, Any]]:
        stores = json.loads(response.text)["coffeeShops"]

        for store in stores:

            yield {
                "addr_full": f"{store.get("address2")}, {store.get("postalCode")} {store.get("city")}",
                "brand": "Espresso House",
                "city": store.get("city"),
                "country": store.get("country"),
                "extras": {
                    "brand": "Espresso House",
                    "fascia": "Espresso House",
                    "category": "Food & Beverage",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
                "name": f" Espresso House {store.get("coffeeShopName")}",
                "opening_hours": self.parse_opening_hours(store.get("openingHours")),
                "phone": store.get("phoneNumber"),
                "postcode": store.get("postalCode"),
                "ref": store.get("coffeeShopId"),
                "state": None,
                "website": f"https://fi.espressohouse.com/en/find-us/{store.get("coffeeShopName","").lower().replace(" ", "-")}",
            }

    def parse_opening_hours(
        self, opening_hours: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        result = {}
        days_maping: Dict[str, Any] = {
            "Monday": "Mon",
            "Tuesday": "Tue",
            "Mittwoch": "Wed",
            "Thursday": "Thu",
            "Friday": "Fri",
            "Saturday": "Sat",
            "Sunday": "Sun",
        }

        for opening_hour in opening_hours:

            result[days_maping.get(opening_hour.get("weekDay", ""))] = (
                f"{opening_hour.get("openFrom", "")[:-3]}-{opening_hour.get("openTo", "")[:-3]}"
                if opening_hour
                else None
            )

        return {"opening_hours": result}
