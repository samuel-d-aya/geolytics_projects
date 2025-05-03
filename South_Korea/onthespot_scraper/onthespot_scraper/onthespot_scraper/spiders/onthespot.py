import json
import datetime
from urllib.parse import urlencode
import scrapy


class OnthespotSpider(scrapy.Spider):
    name = "onthespot"
    allowed_domains = ["www.onthespot.co.kr"]
    start_urls = ["https://www.onthespot.co.kr/board/store/list"]

    cookies = {
        "WMONID": "g7EyvCBVL1P",
        "JSESSIONID": "aaap9Gt0orqFy9zo0YfAzerjJrRMgxMgMXx0Sgk2P99FMOr_bwjZf5XfmTBA",
        "NetFunnel_ID": "",
        "_TBS_NAUIDA_1084": "b01c9747f701090011834426c8e4f300#1746048341#1746048341#1",
        "_TBS_AUIDA_1084": "definedvalue:1",
    }

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Referer": "https://www.onthespot.co.kr/board/store",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        # 'Cookie': 'WMONID=g7EyvCBVL1P; JSESSIONID=aaap9Gt0orqFy9zo0YfAzerjJrRMgxMgMXx0Sgk2P99FMOr_bwjZf5XfmTBA; NetFunnel_ID=; _TBS_NAUIDA_1084=b01c9747f701090011834426c8e4f300#1746048341#1746048341#1; _TBS_AUIDA_1084=definedvalue:1',
    }

    params = {
        "areaNo": "",
        "areaDtlSeq": "",
        "storeGbnCode": "",
        "storeServiceCode": "",
        "storeSearchWord": "",
        "_": "1746054847620",
    }

    def start_requests(self):
        for url in self.start_urls:
            full_url = f"{url}?{urlencode(self.params)}"
            yield scrapy.Request(
                url=full_url,
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse,
            )

    def parse(self, response):
        data = response.json().get("list")

        for store in data:

            yield {
                "addr_full": store.get("postAddrText"),
                "brand": "On The Spot",
                "city": None,
                "country": "South Korea",
                "extras": {
                    "brand": "On The Spot",
                    "fascia": "On The Spot",
                    "category": "Retail",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.get("ypointText"),
                "lon": store.get("xpointText"),
                "name": store.get("storeName"),
                "opening_hours": {
                    "opening_hours": {
                        "Mon": f"{store.get('businessStartTime')}-{store.get('businessEndTime')}",
                        "Tue": f"{store.get('businessStartTime')}-{store.get('businessEndTime')}",
                        "Wed": f"{store.get('businessStartTime')}-{store.get('businessEndTime')}",
                        "Thu": f"{store.get('businessStartTime')}-{store.get('businessEndTime')}",
                        "Fri": f"{store.get('businessStartTime')}-{store.get('businessEndTime')}",
                        "Sat": f"{store.get('businessStartTime')}-{store.get('businessEndTime')}",
                        "Sun": f"{store.get('businessStartTime')}-{store.get('businessEndTime')}",
                    }
                },
                "phone": store.get("tlphnNo"),
                "postcode": store.get("postCodeText"),
                "ref": store.get("storeNo"),
                "state": None,
                "website": "https://www.onthespot.co.kr/board/store",
            }
