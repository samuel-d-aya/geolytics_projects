import json
import scrapy
import datetime
import calendar

# "https://api.hugoboss.eu/s/GLOBAL/dw/shop/v22_10/stores?client_id=871c988f-3549-4d76-b200-8e33df5b45ba&latitude=31.60403597768415&longitude=137.15386460000002&count=100&maxDistance=5462.561151093578&distanceUnit=km&start=0"


class HugoSpider(scrapy.Spider):
    name = "hugo"
    allowed_domains = ["api.hugoboss.eu"]
    api_url = "https://api.hugoboss.eu/s/GLOBAL/dw/shop/v22_10/stores"

    params = {
        "client_id": "871c988f-3549-4d76-b200-8e33df5b45ba",
        "latitude": "31.60403597768415",
        "longitude": "137.15386460000002",
        "count": "100",
        "maxDistance": "5462.561151093578",
        "distanceUnit": "km",
        "start": "0",
    }

    def start_requests(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "X-Requested-With": "XMLHttpRequest",
        }

        
        url = f"{self.api_url}?client_id={self.params['client_id']}&latitude={self.params['latitude']}&longitude={self.params['longitude']}&count={self.params['count']}&maxDistance={self.params['maxDistance']}&distanceUnit={self.params['distanceUnit']}&start={self.params['start']}"
        yield scrapy.Request(url, headers=headers, callback=self.parse)

    def parse(self, response):
        data = json.loads(response.text)
        for store in data.get("data", []):
            print(store.get("store_hours"))
            yield {
                "addr_full": store.get("address1"),
                "brand":"Hugo Boss",
                "city": store.get("city"),
                "country": store.get("country_code"),
                "extras": {
                    "brand": store.get("c_brands"),
                    "fascia": store.get("c_type"),
                    "category": store.get("c_categories"),
                    "edit_date": datetime.datetime.now().strftime('%Y%m%d'),
                    "lat_lon_source": "website",
                },
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
                "name": store.get("name"),
                "opening_hours": (
                    {
                        store.get("c_type"): {
                            calendar.day_name[
                                int(day_num) - 1
                            ][:3]: f"{whours[0]}-{whours[1]}"
                            for day_num, whours in json.loads(
                                store.get("store_hours")
                            ).items()
                        }
                    }
                    if store.get("store_hours")
                    else "Not Available"
                ),
                "phone": store.get("phone"),
                "postcode": store.get("postal_code"),
                "ref": store.get("id"),
                "state": store.get("state_code"),
                "website": f"https://www.hugoboss.com/store#lat={store.get("latitude")}&lng={store.get("longitude")}",
            }


