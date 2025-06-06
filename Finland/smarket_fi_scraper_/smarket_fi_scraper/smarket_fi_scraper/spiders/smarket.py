import json
import datetime
from urllib.parse import urlencode
from typing import Dict, Any, List, Union, Iterator
import scrapy
from scrapy.http.request import Request
from scrapy.http.response import Response


class SmarketSpider(scrapy.Spider):
    name = "smarket"
    allowed_domains = ["api.s-kaupat.fi", "www.s-kaupat.fi"]
    start_urls = ["https://api.s-kaupat.fi/?"]
    detail_page_url = (
        "https://www.s-kaupat.fi/_next/data/eApSa9vPGYZEe-P4GFWI9/myymala/"
    )
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.6",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-nextjs-data": "1",
    }
    detail_params = {
        "slugAndId": [
            "",
            "",
        ],
    }
    brands = ["S_MARKET", "PRISMA"]

    def start_requests(self) -> Iterator[Request]:
        for brand in self.brands:
            variables: Dict[str, Any] = {"query": None, "brand": brand}
            params = {
                "operationName": "RemoteStoreSearch",
                "variables": json.dumps(variables),
                "extensions": '{"persistedQuery":{"version":1,"sha256Hash":"e49317e01c3a57b286fadd6f3ea47fd1d64adebb483943ba0e229307d15763b5"}}',
            }
            full_url = self.start_urls[0] + urlencode(params)
            yield scrapy.Request(
                url=full_url,
                headers=self.headers,
                callback=self.parse,
                meta={"brand": brand},
            )

    def parse(self, response: Response) -> Iterator[Union[Dict[str, Any], Request]]:
        data = json.loads(response.text)["data"]

        stores = data.get("searchStores").get("stores")

        for store in stores:
            full_url = (
                f"https://www.s-kaupat.fi/myymala/{store.get("slug")}/{store.get("id")}"
            )
            yield response.follow(url=full_url, callback=self.parse_all_details)

        cursor = data.get("searchStores").get("cursor")
        self.logger.info(f"\n\n{cursor}\n\n")
        if cursor:
            brand = response.meta.get("brand")
            variables: Dict[str, Any] = {
                "query": None,
                "brand": brand,
                "cursor": cursor,
            }
            params = {
                "operationName": "RemoteStoreSearch",
                "variables": json.dumps(variables),
                "extensions": '{"persistedQuery":{"version":1,"sha256Hash":"e49317e01c3a57b286fadd6f3ea47fd1d64adebb483943ba0e229307d15763b5"}}',
            }

            self.logger.info(f"\n\n{params}\n\n")
            next_url = self.start_urls[0] + urlencode(params)
            yield scrapy.Request(
                url=next_url, headers=self.headers, callback=self.parse
            )

    def parse_all_details(
        self, response: Response
    ) -> Iterator[Union[Dict[str, Any], Request]]:

        page_props = (
            json.loads(response.css("#__NEXT_DATA__::text").get() or "")
            .get("props")
            .get("pageProps")
        )
        # if "__N_REDIRECT" in page_props:
        #     self.detail_params["slugAndId"][0] = response.url.split("/")[-2]
        #     self.detail_params["slugAndId"][1] = response.url.split("/")[-1]

        #     full_url = (
        #         f"https://www.s-kaupat.fi/_next/data/eApSa9vPGYZEe-P4GFWI9{page_props["__N_REDIRECT"]}.json?"
        #         + urlencode(self.detail_params)
        #     )
        #     yield scrapy.Request(
        #         url=full_url, headers=self.headers, callback=self.parse_all_details
        #     )
        # else:
        store = page_props.get("store")
        location = store.get("location").get("address")
        addr = f"{location.get("street").get("default")}, {location.get("postcode")} {location.get("postcodeName").get("default")}"
        yield {
            "addr_full": addr,
            "brand": store.get("brand"),
            "city": location.get("postcodeName").get("default"),
            "country": "Finland",
            "extras": {
                "brand": store.get("brand"),
                "fascia": store.get("brand"),
                "category": "Retail",
                "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                "lat_lon_source": "Third Party",
            },
            "lat": store.get("location").get("coordinates").get("lat"),
            "lon": store.get("location").get("coordinates").get("lon"),
            "name": store.get("name"),
            "opening_hours": self.parse_opening_hours(
                store.get("weeklyOpeningHours")[0].get("openingTimes")
            ),
            "phone": (
                store.get("contactInfo", {})
                .get("phoneNumber", {})
                .get("number", "")
                .replace(" ", "")
                if store.get("contactInfo", {}).get("phoneNumber", {})
                else None
            ),
            "postcode": location.get("postcode"),
            "ref": store.get("id"),
            "state": None,
            "website": response.url,
        }

    def parse_opening_hours(
        self, opening_hours: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        days_maping: Dict[str, Any] = {
            "MON": "Mon",
            "TUE": "Tue",
            "WED": "Wed",
            "THU": "Thu",
            "FRI": "Fri",
            "SAT": "Sat",
            "SUN": "Sun",
        }
        result = {}
        for opening_hour in opening_hours:
            result[days_maping.get(opening_hour.get("day", ""))] = (
                f"{opening_hour.get(
                "ranges", ""
            )[0].get("open", "")}-{opening_hour.get(
                "ranges", ""
            )[0].get("close", "")

            }"
                if opening_hour.get("mode") == "RANGE"
                else "00:00-23:59"
            )

        return {"opening_hours": result}
