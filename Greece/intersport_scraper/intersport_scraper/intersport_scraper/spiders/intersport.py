import datetime
import re
from typing import Iterable, Dict, Any, List
import scrapy
from scrapy.http.request import Request
from scrapy.http.response import Response


class IntersportSpider(scrapy.Spider):
    name = "intersport"
    allowed_domains = ["www.intersport.gr"]
    start_urls = ["https://www.intersport.gr/en/about-us-2/katastimata/"]
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.8",
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
    }

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield scrapy.Request(url=url, headers=self.headers, callback=self.parse)

    def parse(self, response: Response) -> Iterable[Dict[str, Any]]:

        stores = response.css(".center-container .partner-list > li")

        for store in stores:

            yield {
                "addr_full": re.sub(
                    r"\s+",
                    " ",
                    " ".join(store.css(".address-one::text").getall()) or "",
                ),
                "brand": "Intersport",
                "city": re.sub(
                    r"\s+",
                    "",
                    store.css(".address-one::text").getall()[1].split(",")[-1] or "",
                ),
                "country": "Greece",
                "extras": {
                    "brand": "Intersport",
                    "fascia": "Intersport",
                    "category": "Retail",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.css(".box-info::attr(data-latitude)").get(),
                "lon": store.css(".box-info::attr(data-longitude)").get(),
                "name": f"Intersport {store.css(".name::text").get()}",
                "opening_hours": self.parse_opening_hours(
                    store.css(".opening-hours::text").get() or ""
                ),
                "phone": re.sub(
                    r"\s+", "", (store.css(".phone::text").get() or "").split(":")[-1]
                ),
                "postcode": re.sub(
                    r"\s+",
                    "",
                    store.css(".address-one::text").getall()[1].split(",")[0] or "",
                ),
                "ref": (store.css(".more > a::attr(href)").get() or "").split("/~")[-1],
                "state": None,
                "website": response.urljoin(
                    store.css(".more > a::attr(href)").get() or ""
                ),
            }

    def parse_opening_hours(self, text: str) -> Dict[str, Any]:
        days_map = {
            "monday": "Mon",
            "mon": "Mon",
            "tuesday": "Tue",
            "tue": "Tue",
            "wednesday": "Wed",
            "wed": "Wed",
            "thursday": "Thu",
            "thu": "Thu",
            "friday": "Fri",
            "fri": "Fri",
            "saturday": "Sat",
            "sat": "Sat",
            "sunday": "Sun",
            "sun": "Sun",
        }

        days_ordered = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        def normalize_time(t: str) -> str:
            return (
                t.replace(".", ":").zfill(5)
                if ":" in t or "." in t
                else f"{t.zfill(2)}:00"
            )

        def expand_days(start: str, end: str) -> List[str]:
            try:
                i, j = days_ordered.index(start), days_ordered.index(end)
                return days_ordered[i : j + 1]
            except ValueError:
                return []

        text = text.lower()
        text = text.replace("through", "to").replace("thru", "to")
        parts = re.split(r"\s*\|\s*", text)
        result = {}

        for part in parts:
            day_match = re.match(r"([a-z\.]+)(?:\s*(?:-|to)\s*([a-z\.]+))?", part)
            if not day_match:
                continue
            d1 = day_match.group(1).strip(".")
            d2 = day_match.group(2).strip(".") if day_match.group(2) else d1
            d1_std = days_map.get(d1)
            d2_std = days_map.get(d2)
            if not d1_std or not d2_std:
                continue
            days = expand_days(d1_std, d2_std)

            time_match = re.search(
                r"(\d{1,2}[:\.]?\d{0,2})\s*[-–]\s*(\d{1,2}[:\.]?\d{0,2})", part
            )
            if time_match:
                open_time = normalize_time(time_match.group(1))
                close_time = normalize_time(time_match.group(2))
                time_range = f"{open_time}-{close_time}"
                for day in days:
                    result[day] = time_range

        return {"opening_hours": result}
