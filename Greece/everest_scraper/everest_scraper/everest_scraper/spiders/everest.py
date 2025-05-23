import json
import datetime
import requests
import re
from urllib.parse import urlencode
from scrapy.selector import Selector
import scrapy


class EverestSpider(scrapy.Spider):
    name = "everest"
    allowed_domains = ["www.everest.gr"]
    start_urls = [
        "https://www.everest.gr/en/ajax/Atcom.Sites.Everest.Components.StoreFinder.GetStores/"
    ]
    opening_hour_endpoint = "https://www.everest.gr/en/ajax/Atcom.Sites.Everest.Components.StoreFinder.StoreGeneralInfo/"
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://www.everest.gr",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://www.everest.gr/en/stores/",
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    data = {
        "browserlat": "",
        "browserlng": "",
    }
    params = {
        "fullContent": "True",
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                method="POST",
                url=url,
                headers=self.headers,
                body=json.dumps(self.data),
                callback=self.parse,  # type: ignore
            )

    def parse(self, response):  # type: ignore
        data = json.loads(response.text)  # type: ignore

        stores = data.get("results")

        for store in stores:

            store_id = store.get("ID") or store.get("StoreStateInfo").get(
                "StoreViewInfo"
            ).get("ID")
            data = {
                "storeID": store_id,
            }
            opening_hour_response = requests.post(
                url=self.opening_hour_endpoint,
                params=self.params,
                headers=self.headers,
                data=data,
                timeout=1800,
            )

            yield {  # type: ignore
                "addr_full": store.get("Address")
                or store.get("StoreStateInfo").get("StoreViewInfo").get("Address"),
                "brand": "Everest",
                "city": None,
                "country": "Greece",
                "extras": {
                    "brand": "Everest",
                    "fascia": "Everest",
                    "category": "Food & Beverage",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Google",
                },
                "lat": store.get("Lat")
                or store.get("StoreStateInfo").get("StoreViewInfo").get("Lat"),
                "lon": store.get("Lng")
                or store.get("StoreStateInfo").get("StoreViewInfo").get("Lng"),
                "name": f"Everest { store.get("Region") or store.get("Name") or store.get("StoreStateInfo").get("StoreViewInfo").get("Name")}",
                "opening_hours": self.parse_opening_hours(opening_hour_response),  # type: ignore
                "phone": store.get("phone")
                or store.get("StoreStateInfo").get("StoreViewInfo").get("PhoneNumber"),
                "postcode": store.get("ZipCode")
                or store.get("StoreStateInfo").get("StoreViewInfo").get("ZipCode"),
                "ref": store.get("ID")
                or store.get("StoreStateInfo").get("StoreViewInfo").get("ID"),
                "state": None,
                "website": "https://www.everest.gr/en/stores/",  # type: ignore
            }

    def parse_opening_hours(self, opening_hour):  # type: ignore

        output = Selector(text=opening_hour.text)  # type: ignore

        days_mapping = {
            "Monday": "Mon",
            "Tuesday": "Tue",
            "Wednesday": "Wed",
            "Thursday": "Thu",
            "Friday": "Fri",
            "Saturday": "Sat",
            "Sunday": "Sun",
        }
        opening_hours = output.css("li")  # type: ignore

        print(f"\n\n{output.get()}\n\n")

        if not opening_hours:
            return {"opening_hour": {}}  # type: ignore

        result = {  # type: ignore
            days_mapping.get(wk_day.css(".day::text").get()): (  # type: ignore
                re.sub(r"\s+", " ", wk_day.css(".hour_range > span::text").get())  # type: ignore
                if re.sub(r"\s+", " ", wk_day.css(".hour_range > span::text").get())  # type: ignore
                != "All day"
                else "00:00-23:59"
            )
            for wk_day in output.css(".store-section li")
        }
        return {"opening_hour": result}  # type: ignore
