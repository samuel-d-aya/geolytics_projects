from typing import Iterable, Dict, Tuple, Any, List
import datetime
import json
import scrapy
from scrapy.http.request import Request
from scrapy.http.response import Response
from scrapy_playwright.page import PageMethod


class PlaisioSpider(scrapy.Spider):
    name = "plaisio"
    allowed_domains = ["www.plaisio.gr"]
    start_urls = ["https://www.plaisio.gr/Store-Locator"]

    cookies = {
        "ConstructorioID_client_id": "f1a78d26-1a13-4fb7-ba9a-02b2400da2b0",
        "pls_uid": "sessionId=c9ff3107-a0fc-452b-a584-32286b849de9&userId=c9ff3107-a0fc-452b-a584-32286b849de9&userEmail=&ip=194.187.251.231",
        "azuappgwplsgr": "02c20b95be8296d50d4c85b6f98d96d2d6f577f8e7f245110e24af3c329998c6",
        "azuappgwplsgrCORS": "02c20b95be8296d50d4c85b6f98d96d2d6f577f8e7f245110e24af3c329998c6",
        "ConstructorioID_session_id": "4",
        "chatObject": "%7B%22userInput%22:%7B%22email%22:%22%22,%22selectedDepartment%22:%220%22,%22message%22:%22%22%7D,%22isValidEmail%22:false,%22chatResponse%22:%7B%22sessionKey%22:%22%22,%22contactId%22:0,%22isInService%22:false,%22messages%22:%22%22,%22result%22:%7B%22extensionData%22:null,%22sessionKey%22:%22%22,%22anonymousUsername%22:%22%22,%22anonymousID%22:0%7D,%22isDisconnected%22:false,%22activeSkillSets%22:%5B%5D%7D,%22queueInfo%22:%7B%22sessionKey%22:%22%22,%22contactId%22:0%7D,%22pollingTimer%22:0,%22typingStart%22:false,%22typingTimer%22:null%7D",
        "ConstructorioID_session": '{"sessionId":4,"lastTime":1748375491414}',
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.6",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        # 'cookie': 'ConstructorioID_client_id=f1a78d26-1a13-4fb7-ba9a-02b2400da2b0; pls_uid=sessionId=c9ff3107-a0fc-452b-a584-32286b849de9&userId=c9ff3107-a0fc-452b-a584-32286b849de9&userEmail=&ip=194.187.251.231; azuappgwplsgr=02c20b95be8296d50d4c85b6f98d96d2d6f577f8e7f245110e24af3c329998c6; azuappgwplsgrCORS=02c20b95be8296d50d4c85b6f98d96d2d6f577f8e7f245110e24af3c329998c6; ConstructorioID_session_id=4; chatObject=%7B%22userInput%22:%7B%22email%22:%22%22,%22selectedDepartment%22:%220%22,%22message%22:%22%22%7D,%22isValidEmail%22:false,%22chatResponse%22:%7B%22sessionKey%22:%22%22,%22contactId%22:0,%22isInService%22:false,%22messages%22:%22%22,%22result%22:%7B%22extensionData%22:null,%22sessionKey%22:%22%22,%22anonymousUsername%22:%22%22,%22anonymousID%22:0%7D,%22isDisconnected%22:false,%22activeSkillSets%22:%5B%5D%7D,%22queueInfo%22:%7B%22sessionKey%22:%22%22,%22contactId%22:0%7D,%22pollingTimer%22:0,%22typingStart%22:false,%22typingTimer%22:null%7D; ConstructorioID_session={"sessionId":4,"lastTime":1748375491414}',
    }

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                headers=self.headers,
                cookies=self.cookies,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                    ],
                },
                callback=self.parse,
            )

    def parse(self, response: Response) -> Iterable[Dict[str, Any]]:
        script_text = response.css(".location-locator-page >  script::text").get() or ""
        stores = self.parse_script_text(script_text)
        for store in stores:

            yield {
                "addr_full": f"{store.get("addressLine1") or store.get("addressLine2") }, {store.get("city")}",
                "brand": "Plaisio",
                "city": store.get("city"),
                "country": "Greece",
                "extras": {
                    "brand": "Plaisio",
                    "fascia": "Plaisio",
                    "category": "Retail",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
                "name": f"Plasio {store.get("locationName")}",
                "opening_hours": self.parse_opening_hours(
                    store.get("openingHours") or [{}]
                ),
                "phone": store.get("phoneNumber"),
                "postcode": store.get("postalCode"),
                "ref": store.get("locationNumber"),
                "state": store.get("county"),
                "website": f"https://www.plaisio.gr{store.get("url")}",
            }

    def parse_script_text(self, script_text: str) -> List[Dict[str, Any]]:
        """
        More robust version that handles nested objects and arrays.
        """
        try:
            # Find the start of locations array
            locations_start = script_text.find('"locations":')
            if locations_start == -1:
                return []

            # Find the opening bracket
            bracket_start = script_text.find("[", locations_start)
            if bracket_start == -1:
                return []

            # Count brackets to find the matching closing bracket
            bracket_count = 0
            i = bracket_start
            while i < len(script_text):
                if script_text[i] == "[":
                    bracket_count += 1
                elif script_text[i] == "]":
                    bracket_count -= 1
                    if bracket_count == 0:
                        # Found the matching closing bracket
                        locations_json = script_text[bracket_start : i + 1]
                        return json.loads(locations_json)
                i += 1

            return []

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing locations: {e}")
            return []

    def parse_opening_hours(
        self, opening_hours: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        result = {}

        for day, workhr in zip(days, opening_hours):
            result[day] = workhr.get("regular")

        return {"opening_hours": result}
