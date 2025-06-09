import re
import json
import datetime
from typing import Iterable, Dict, Any
from urllib.parse import urlencode
import scrapy
from scrapy.http.response import Response
from scrapy.http.request import Request


class NenechickenSpider(scrapy.Spider):
    name = "nenechicken"
    allowed_domains = ["nenechicken.com"]
    start_urls = ["https://nenechicken.com/process/SEARCH_STORE.fuse?"]
    detail_url = ["https://nenechicken.com/process/storeDetail.fuse?"]

    cookies = {
        "PUID": "D87AAEF6C61D4AADAF732D510BA0306A",
        "ASPSESSIONIDSGDDSBQA": "MJMILDOAPKMIHGEOKJBHLBIG",
        "1:1626_1": "1:1626_1_to_9c:349",
    }

    headers = {
        "Accept": "text/html, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://nenechicken.com",
        "Pragma": "no-cache",
        "Referer": "https://nenechicken.com/home_shop.asp",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    params = {
        "LARGE_AREA": "",
        "MID_AREA": "",
        "S_WORD": "",
        "VIEW_ONOFF": "ALL",
    }

    detail_params = {
        "cust_code": "",
    }

    data = {
        "VIEW_ONOFF": "ALL",
        "PIZZA_ONOFF": "N",
        "DELIVERY_ONOFF": "N",
        "TAKEOUT_ONOFF": "N",
        "LARGE_AREA": "",
        "MId_AREA": "",
        "S_WORD": "",
    }

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            full_url = url + urlencode(self.params)
            yield scrapy.Request(
                method="POST",
                url=full_url,
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse,
                body=json.dumps(self.data),
            )

    def parse(self, response: Response):
        stores = response.css(".storeinfo::attr(onclick)").getall()

        for store in stores:
            match = re.search(
                r"changeMapCenter2\('([^']+)','([^']+)'\);\s*CUSTDETAIL\('(\d+)'\)",
                store or "",
            )
            if match:
                lat, lon, detail_id = match.groups()
                self.detail_params["cust_code"] = detail_id
                full_url = self.detail_url[0] + urlencode(self.detail_params)
                yield response.follow(
                    full_url,
                    method="POST",
                    callback=self.parse_details,
                    meta={"lat": lat, "lon": lon, "id": detail_id},
                )

    def parse_details(self, response: Response) -> Iterable[Dict[str, Any]]:
        name = response.css(".tit::text").get()
        address = response.css("tr:nth-child(1) .InfoTxt::text").get()
        phone = response.css("tr:nth-child(2) .InfoTxt::text").get()
        raw_hours = response.css("tr:nth-child(3) .InfoTxt::text").get()

        yield {
            "addr_full": self.clean_field(address),
            "brand": "Nenechicken",
            "city": None,
            "country": "Korea",
            "extras": {
                "brand": "Nenechicken",
                "fascia": "Nenechicken",
                "category": "Restaurant",
                "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                "lat_lon_source": "From HTML onclick",
            },
            "lat": response.meta.get("lat"),
            "lon": response.meta.get("lon"),
            "name": f"Nenechicken {name.strip() if name else ''}",
            "opening_hours": self.parse_opening_hours(
                self.clean_field(raw_hours).replace("~", "-") if raw_hours else None
            ),
            "phone": self.clean_field(phone),
            "postcode": None,
            "ref": response.meta.get("id"),
            "state": None,
            "website": "https://nenechicken.com/home_shop.asp",
        }

    def clean_field(self, text: str) -> str:
        if not text:
            return None
        clean = re.sub(r"\s+", " ", text).strip()
        return clean if clean else None

    def parse_opening_hours(self, operation_time: str) -> Dict[str, Any]:
        if not operation_time:
            return {"opening_hours": {}}

        result = {}
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            result[day] = operation_time

        return {"opening_hours": result}
