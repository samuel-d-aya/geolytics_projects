import re
import datetime
import json
import scrapy
from scrapy.selector import Selector


class NorthfaceSpider(scrapy.Spider):
    name = "northface"
    allowed_domains = ["thenorthface.com.au"]
    start_urls = ["https://thenorthface.com.au/stores/"]
    cookies = {
        "dwac_1b330a534e4475508c9f3f8492": "V4ZbkHhoqFDbshWCzT5mYmMRTqV71hIeNKc%3D|dw-only|||AUD|false|Australia%2FSydney|true",
        "cqcid": "bcBFsyawKlyqmMBlbuqGeGFBHz",
        "cquid": "||",
        "dwanonymous_284e29b98ff0c5ba308f7c6557daef7d": "bcBFsyawKlyqmMBlbuqGeGFBHz",
        "sid": "V4ZbkHhoqFDbshWCzT5mYmMRTqV71hIeNKc",
        "__cq_dnt": "0",
        "dw_dnt": "0",
        "dwsid": "_4E3cRGx-U375nYSb0qIXMsWIkQSD0MDFPNr9XBfGV6IUahIVyZREmfyBc1_5VMD862sXo3m_x7GceWNozECxg==",
        "KP_UIDz-ssn": "02Ma6FxjLPJURXFRVJXiUs7jqSysXhHatHSDWgGw3M8O4JapWfHynVhwEXUkfdOHETBu4FSGhYjmExWPWIcMgx6MNuX4zW89uByHkXBk044Qfisc17K7m2reYGuI9pGVqWtTjWYaN02Cp2U8JjGCmYlP3uoGN3G76ceJg3MdFg",
        "KP_UIDz": "02Ma6FxjLPJURXFRVJXiUs7jqSysXhHatHSDWgGw3M8O4JapWfHynVhwEXUkfdOHETBu4FSGhYjmExWPWIcMgx6MNuX4zW89uByHkXBk044Qfisc17K7m2reYGuI9pGVqWtTjWYaN02Cp2U8JjGCmYlP3uoGN3G76ceJg3MdFg",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.5",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://thenorthface.com.au/stores/",
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        # 'cookie': 'dwac_1b330a534e4475508c9f3f8492=V4ZbkHhoqFDbshWCzT5mYmMRTqV71hIeNKc%3D|dw-only|||AUD|false|Australia%2FSydney|true; cqcid=bcBFsyawKlyqmMBlbuqGeGFBHz; cquid=||; dwanonymous_284e29b98ff0c5ba308f7c6557daef7d=bcBFsyawKlyqmMBlbuqGeGFBHz; sid=V4ZbkHhoqFDbshWCzT5mYmMRTqV71hIeNKc; __cq_dnt=0; dw_dnt=0; dwsid=_4E3cRGx-U375nYSb0qIXMsWIkQSD0MDFPNr9XBfGV6IUahIVyZREmfyBc1_5VMD862sXo3m_x7GceWNozECxg==; KP_UIDz-ssn=02Ma6FxjLPJURXFRVJXiUs7jqSysXhHatHSDWgGw3M8O4JapWfHynVhwEXUkfdOHETBu4FSGhYjmExWPWIcMgx6MNuX4zW89uByHkXBk044Qfisc17K7m2reYGuI9pGVqWtTjWYaN02Cp2U8JjGCmYlP3uoGN3G76ceJg3MdFg; KP_UIDz=02Ma6FxjLPJURXFRVJXiUs7jqSysXhHatHSDWgGw3M8O4JapWfHynVhwEXUkfdOHETBu4FSGhYjmExWPWIcMgx6MNuX4zW89uByHkXBk044Qfisc17K7m2reYGuI9pGVqWtTjWYaN02Cp2U8JjGCmYlP3uoGN3G76ceJg3MdFg',
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, headers=self.headers, cookies=self.cookies, callback=self.parse  # type: ignore
            )

    def parse(self, response):  # type: ignore
        data = json.loads(response.css(".jumbotron::attr(data-locations)").get())  # type: ignore

        for store in data:

            store_info = Selector(text=store.get("infoWindowHtml")).css(
                ".store-details"
            )

            yield {
                "addr_full": re.sub(
                    r"\s+", " ", store_info.css(".store-map::text").get()  # type: ignore
                ),  # type: ignore
                "brand": "The North Face",
                "city": None,
                "country": "Autrialia",
                "extras": {
                    "brand": "The North Face",
                    "fascia": "The North Face",
                    "category": "Retail",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
                "name": f"The North Face {store.get("name")}",
                "opening_hours": {
                    "Opening_hours": {
                        "Mon": "00:00-23:59",
                        "Tue": "00:00-23:59",
                        "Wed": "00:00-23:59",
                        "Thu": "00:00-23:59",
                        "Fri": "00:00-23:59",
                        "Sat": "00:00-23:59",
                        "Sun": "00:00-23:59",
                    }
                },
                "phone": None,
                "postcode": None,
                "ref": store_info.css("::attr(data-store-id)").get(),
                "state": None,
                "website": store_info.css(".store-name > a::attr(href)").get(),
            }
