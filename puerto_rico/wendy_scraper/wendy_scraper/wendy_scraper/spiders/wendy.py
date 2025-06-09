from typing import Iterable, Dict, Any
import datetime
import re
import scrapy
from scrapy.http.request import Request
from scrapy.http.response import Response
from ..utils import parse_js_object_to_dict, parse_business_hours
from scrapy.selector.unified import Selector


class WendySpider(scrapy.Spider):
    name = "wendy"
    allowed_domains = ["www.grupocolongerena.com"]
    start_urls = ["https://www.grupocolongerena.com/wendys"]

    headers = {
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield scrapy.Request(url=url, headers=self.headers, callback=self.parse)

    def parse(self, response: Response) -> Iterable[Dict[str, Any]]:

        script_text = response.css("script:nth-child(3)::text").get()
        matches = re.findall(
            r"gj\[\d+]\s*=\s*({.*?});",
            script_text or "",
            re.DOTALL,
        )

        for match in matches:
            store = parse_js_object_to_dict(match)

            addr = store.get("location") or ""
            city_match = re.search(r"(\S+)\s*,?\s*P\.R", addr)
            city = city_match.group(1) if city_match else ""
            post_match = re.search(r"P\.R\.?\s*(\S+)", addr)
            postal = post_match.group(1) if post_match else ""

            yield {
                "addr_full": addr,
                "brand": "Wendy's",
                "city": city,
                "country": "Puerto Rico",
                "extras": {
                    "brand": "Wendy's",
                    "fascia": "Wendy's",
                    "category": "Retail",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Google",
                },
                "lat": store.get("lat"),
                "lon": store.get("lng"),
                "name": store.get("name"),
                "opening_hours": parse_business_hours(
                    Selector(text=store.get("address")).css("li::text").getall()
                    or Selector(text=store.get("address")).css("p::text").getall()
                    or [store.get("hours") if len(store.get("hours", "")) > 5 else ""]
                    or [""]
                ),
                "phone": store.get("phone"),
                "postcode": postal,
                "ref": store.get("id"),
                "state": store.get("state"),
                "website": response.url,
            }
