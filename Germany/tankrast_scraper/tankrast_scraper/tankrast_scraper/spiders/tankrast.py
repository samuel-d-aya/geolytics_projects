import scrapy
import json
import datetime 


class LocationsSpider(scrapy.Spider):
    name = "locations"
    allowed_domains = ["www.raststaetten.de"]
    start_urls = ["https://www.raststaetten.de/locations.json"]

    custom_headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "connection": "keep-alive",
        "cookie": "map_intro=0",
        "host": "www.raststaetten.de",
        "referer": "https://www.raststaetten.de/",
        "sec-ch-ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            headers=self.custom_headers,
            callback=self.parse
        )

    def parse(self, response):
        data = json.loads(response.text)
        for location in data.get("locations", []):
            yield {
                "ref": location.get("uid"),
                "name": location.get("title"),
                "extras": {
                    "brand": "Public",
                    "fascia": "Public",
                    "category": "Retail",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Third Party",
                },
                "lat": location.get("latitude"),
                "lon": location.get("longitude"),
                "postcode": location.get("highway"),
                "city": location.get("city"),
                "zip": location.get("zip"),
                "website": location.get("urlPage")
            }
