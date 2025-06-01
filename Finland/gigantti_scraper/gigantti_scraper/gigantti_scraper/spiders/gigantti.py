import json
import datetime
from typing import Iterable, Dict, Any, List
import scrapy
from scrapy.http.request import Request
from scrapy.http.response import Response


class GiganttiSpider(scrapy.Spider):
    name = "gigantti"
    allowed_domains = ["www.gigantti.fi"]
    start_urls = ["https://www.gigantti.fi/api/stores"]
    cookies = {
        "_vcrcs": "1.1747858882.3600.ZWZkZDBlNzVmOWZjZTA1NDY5OTMxNTA4OWJjYWMzYzY=.101fc761847314a2197c9ffa9ad92765",
        "locale": "fi",
        "sessionv2": "19d9dadc-7e15-4c45-8102-9d8906e7df02%231747858883201",
        "_bamls_cuid": "zqw2dbDIWKgQXI9hweqY",
        "CookieInformationConsent": "%7B%22website_uuid%22%3A%22806ef00f-64ee-4fb7-b3f1-11cf4b723213%22%2C%22timestamp%22%3A%222025-05-21T20%3A21%3A36.739Z%22%2C%22consent_url%22%3A%22https%3A%2F%2Fwww.gigantti.fi%2F%22%2C%22consent_website%22%3A%22gigantti.fi%22%2C%22consent_domain%22%3A%22www.gigantti.fi%22%2C%22user_uid%22%3A%2266a92362-5c54-4d89-b7d9-75e3918b6c0d%22%2C%22consents_approved%22%3A%5B%22cookie_cat_necessary%22%5D%2C%22consents_denied%22%3A%5B%22cookie_cat_functional%22%2C%22cookie_cat_statistic%22%2C%22cookie_cat_marketing%22%2C%22cookie_cat_unclassified%22%5D%2C%22user_agent%22%3A%22Mozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F136.0.0.0%20Safari%2F537.36%22%7D",
        "_bamls_usid": "0196f482-15d2-7489-a1bc-3e20bdb62673",
    }

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://www.gigantti.fi/",
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        # 'cookie': '_vcrcs=1.1747858882.3600.ZWZkZDBlNzVmOWZjZTA1NDY5OTMxNTA4OWJjYWMzYzY=.101fc761847314a2197c9ffa9ad92765; locale=fi; sessionv2=19d9dadc-7e15-4c45-8102-9d8906e7df02%231747858883201; _bamls_cuid=zqw2dbDIWKgQXI9hweqY; CookieInformationConsent=%7B%22website_uuid%22%3A%22806ef00f-64ee-4fb7-b3f1-11cf4b723213%22%2C%22timestamp%22%3A%222025-05-21T20%3A21%3A36.739Z%22%2C%22consent_url%22%3A%22https%3A%2F%2Fwww.gigantti.fi%2F%22%2C%22consent_website%22%3A%22gigantti.fi%22%2C%22consent_domain%22%3A%22www.gigantti.fi%22%2C%22user_uid%22%3A%2266a92362-5c54-4d89-b7d9-75e3918b6c0d%22%2C%22consents_approved%22%3A%5B%22cookie_cat_necessary%22%5D%2C%22consents_denied%22%3A%5B%22cookie_cat_functional%22%2C%22cookie_cat_statistic%22%2C%22cookie_cat_marketing%22%2C%22cookie_cat_unclassified%22%5D%2C%22user_agent%22%3A%22Mozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F136.0.0.0%20Safari%2F537.36%22%7D; _bamls_usid=0196f482-15d2-7489-a1bc-3e20bdb62673',
    }

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, headers=self.headers, cookies=self.cookies, callback=self.parse
            )

    def parse(self, response: Response) -> Iterable[Dict[str, Any]]:
        stores = json.loads(response.text)["data"]["stores"]

        for store in stores:

            yield {
                "addr_full": f"{store.get("address").get("street")} {store.get("address").get("nr")}, {store.get("address").get("zip")} {store.get("address").get("city")}",
                "brand": "Gigantti",
                "city": store.get("address").get("city"),
                "country": "Finland",
                "extras": {
                    "brand": "Gigantti",
                    "fascia": "Gigantti",
                    "category": "Retail",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.get("address").get("location").get("lat"),
                "lon": store.get("address").get("location").get("lng"),
                "name": store.get("displayName"),
                "opening_hours": self.parse_opening_hours(
                    store.get("openHours").get("days")
                ),
                "phone": None,
                "postcode": store.get("address").get("zip"),
                "ref": store.get("id"),
                "state": None,
                "website": f"https://www.gigantti.fi/{store.get("url")}",
            }

    def parse_opening_hours(self, opening_hours: List[List[str]]) -> Dict[str, Any]:
        result = {}
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for day, time in zip(days, opening_hours):

            result[day] = f"{time[0][0]}:00-{time[1][0]}:00" if time else None

        return {"opening_hours": result}
