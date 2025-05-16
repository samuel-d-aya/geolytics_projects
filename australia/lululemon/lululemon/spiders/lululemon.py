import scrapy
import json
import datetime
from urllib.parse import urlencode

class LululemonSpider(scrapy.Spider):
    name = 'lululemon'
    allowed_domains = ['lululemon.com.au']

    cities = [
        {"city": "Sydney", "lat": -33.8688, "lon": 151.2093},
        {"city": "Newcastle", "lat": -32.9283, "lon": 151.7817},
        {"city": "Wollongong", "lat": -34.4278, "lon": 150.8931},
        {"city": "Melbourne", "lat": -37.8136, "lon": 144.9631},
        {"city": "Geelong", "lat": -38.1499, "lon": 144.3617},
        {"city": "Sorrento", "lat": -38.3394, "lon": 144.7433},
        {"city": "Brisbane", "lat": -27.4698, "lon": 153.0251},
        {"city": "Carindale", "lat": -27.5053, "lon": 153.1027},
        {"city": "Gold Coast", "lat": -28.0167, "lon": 153.4000},
        {"city": "Adelaide", "lat": -34.9285, "lon": 138.6007},
        {"city": "Perth", "lat": -31.9505, "lon": 115.8605},
        {"city": "Hobart", "lat": -42.8821, "lon": 147.3272},
    ]

    def start_requests(self):
        base_url = "https://www.lululemon.com.au/on/demandware.store/Sites-AU-Site/en_AU/Stores-FindStores"

        headers = {
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.lululemon.com.au/en-au/store-locator",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.lululemon.com.au",
             
              }

        for city in self.cities:
            params = [
                ("showMap", "false"),
                ("radius", "300"),
                ("lat", city["lat"]),
                ("long", city["lon"]),
                ("lat", city["lat"]),
                ("long", city["lon"]),
            ]
            query_string = urlencode(params)
            url = f"{base_url}?{query_string}"

            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                meta={"city": city["city"]}
            )

    def parse(self, response):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to decode JSON from response: {response.url}")
            return

        stores = data.get("stores", [])
        for store in stores:
            yield {
                "addr_full": store.get("address1"),
                "city": store.get("city"),
                "country": store.get("countryCode"),
                "brand": "Lululemon",
                "extras": {
                    "brand": "Lululemon",
                    "fascia": "lululemon",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Third Party"
                },
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
                "opening_hours": self.parse_opening_hours(store),
                "name": store.get("name"),
                "phone": store.get("phone"),
                "ref": store.get("ID"),
                "postCode": store.get("postalCode"),
                "state": store.get("stateCode"),
                "website": "https://www.lululemon.com.au/en-au/store-locator"
            }
            
    def parse_opening_hours(self, store):
        days = {
            "mon": "Mon",
            "tue": "Tue",
            "wed": "Wed",
            "thu": "Thu",
            "fri": "Fri",
            "sat": "Sat",
            "sun": "Sun"
        }
        opening_hours = {}

        for short, full in days.items():
            open_key = f"{short}Open"
            close_key = f"{short}Close"

            open_time = store.get(open_key)
            close_time = store.get(close_key)

            if open_time and close_time:
                opening_hours[full] = f"{open_time}-{close_time}"

        return opening_hours
