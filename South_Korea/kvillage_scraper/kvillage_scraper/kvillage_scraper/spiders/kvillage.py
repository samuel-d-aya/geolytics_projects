import datetime
import json
import scrapy


class KvillageSpider(scrapy.Spider):
    name = "kvillage"
    allowed_domains = ["www.k-village.co.kr"]
    start_urls = ["https://www.k-village.co.kr/customer/store/storeList"]

    cookies = {
        "fec3fe3b-123e-4583-b047-6bfe3210ee28": "59fcbd5d-4fbd-4141-af9c-5e11357a020f",
        "exelbid-uid": "EPXSnTtr1oSfJVgHMRX6",
        "fec3fe3b-123e-4583-b047-6bfe3210ee28": "8c6cda14-4c4d-4640-aae4-dfb443300110",
        "JSESSIONID": "NjMyNjI0YzMtYTY1ZS00ODA0LWE2ZGUtOGViZmJjNDJkYWNi",
    }

    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json; charset=UTF-8",
        "origin": "https://www.k-village.co.kr",
        "priority": "u=1, i",
        "referer": "https://www.k-village.co.kr/customer/store",
        "sec-ch-ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        # 'cookie': 'fec3fe3b-123e-4583-b047-6bfe3210ee28=59fcbd5d-4fbd-4141-af9c-5e11357a020f; exelbid-uid=EPXSnTtr1oSfJVgHMRX6; fec3fe3b-123e-4583-b047-6bfe3210ee28=8c6cda14-4c4d-4640-aae4-dfb443300110; JSESSIONID=NjMyNjI0YzMtYTY1ZS00ODA0LWE2ZGUtOGViZmJjNDJkYWNi',
    }

    data = {}

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                method="POST",
                headers=self.headers,
                body=json.dumps(self.data),
                cookies=self.cookies,
                callback=self.parse,
            )

    def parse(self, response):
        data = response.json().get("response").get("storeList")

        for store in data:

            yield {
                "addr_full": store.get("rdnmAdrs"),
                "brand": "K2 Group",
                "city": store.get("metro"),
                "country": "South Korea",
                "extras": {
                    "brand": "K2 Group",
                    "fascia": "K2 Group",
                    "category": "Retail",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "website",
                },
                "lat": store.get("ltd"),
                "lon": store.get("lngtd"),
                "name": store.get("storeFrnm"),
                "opening_hours": {
                    "opening_hours": {
                        "Mon": "00:00-23:59",
                        "Tue": "00:00-23:59",
                        "Wed": "00:00-23:59",
                        "Thu": "00:00-23:59",
                        "Fri": "00:00-23:59",
                        "Sat": "00:00-23:59",
                        "Sun": "00:00-23:59",
                    }
                },
                "phone": store.get("tlphnNo"),
                "postcode": None,
                "ref": f'{store.get("ltd")}-{store.get("lngtd")}',
                "state": store.get("sg"),
                "website": "https://www.k-village.co.kr/customer/store",
            }
