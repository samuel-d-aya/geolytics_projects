import re
import datetime
from urllib.parse import urlencode
import json
import scrapy


class KotsovolosSpider(scrapy.Spider):
    name = "kotsovolos"
    allowed_domains = ["www.kotsovolos.gr", "assets.kotsovolos.gr"]
    start_urls = ["https://www.kotsovolos.gr/StoresLocator"]

    main_endpoint = "https://www.kotsovolos.gr/api/ext/ts/store/10151/storelocator/latitude/39.0742/longitude/21.8243?"

    cookies = {
        "next-auth.csrf-token": "819463c392b759e033faf1052657fad7288773de149c9c423357be1ff899d6ee%7C6a393d4ee453d2100fce6446d5d7a149cfaa752eb03ba5c60fe4837d08e693dc",
        "next-auth.callback-url": "http%3A%2F%2Flocalhost%3A3000",
        "WCToken": "287660571%252CuQzW3lr5029n1LdNxfdFTDwRNk7FgKqcPdlRn4dws79Vi5vY9h10IjlKt0ExLKYbhz1QDvhBG8XcGHl1Sshk6h47yJL5b9mE9CWzTR2xr2tu4VWnMnm3U96tNitJPsBj4mq5WP21s0PKewCaCOWWTT%252Fi1NxC9C1gf9oHk%252BDfQBY3k6LvDsSmYberBe5NRFo%252B1gB4BbPFx%252FtAT8d369rE5Xy5Ua30tHsraUxM0QGHBdoMS2dhwuamVzW7nQuAknojwFIpdbwA2G%252Fq3%252FIpM%252FiE%252BA%253D%253D",
        "WCTrustedToken": "287660571%252C6U2gV84D81VPuKQxhadeTdaAEn%252FlpEm5Vt7CursXxzc%253D",
        "WC_SESSION_ESTABLISHED": "true",
        "GUEST_SESSION": "true",
        "cartData": "%5B%5D",
        "WC_PERSISTENT": "w78tdcYGEYfbxl1%2BQgFnNem5g1fyo0VjxFMf4FL6DSo%3D%3B2025-05-09+15%3A12%3A42.15_1746792762150-814288_0",
        "AKA_A2": "A",
        "JSESSIONID": "0000qP7bMUJSN80vfnA5ERQuHn6:-1",
        "REFERRER": "https%3A%2F%2Fwww.kotsovolos.gr%2Fstore%2Fioannina-spot",
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://www.kotsovolos.gr/StoresLocator",
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        # 'cookie': 'next-auth.csrf-token=819463c392b759e033faf1052657fad7288773de149c9c423357be1ff899d6ee%7C6a393d4ee453d2100fce6446d5d7a149cfaa752eb03ba5c60fe4837d08e693dc; next-auth.callback-url=http%3A%2F%2Flocalhost%3A3000; WCToken=287660571%252CuQzW3lr5029n1LdNxfdFTDwRNk7FgKqcPdlRn4dws79Vi5vY9h10IjlKt0ExLKYbhz1QDvhBG8XcGHl1Sshk6h47yJL5b9mE9CWzTR2xr2tu4VWnMnm3U96tNitJPsBj4mq5WP21s0PKewCaCOWWTT%252Fi1NxC9C1gf9oHk%252BDfQBY3k6LvDsSmYberBe5NRFo%252B1gB4BbPFx%252FtAT8d369rE5Xy5Ua30tHsraUxM0QGHBdoMS2dhwuamVzW7nQuAknojwFIpdbwA2G%252Fq3%252FIpM%252FiE%252BA%253D%253D; WCTrustedToken=287660571%252C6U2gV84D81VPuKQxhadeTdaAEn%252FlpEm5Vt7CursXxzc%253D; WC_SESSION_ESTABLISHED=true; GUEST_SESSION=true; cartData=%5B%5D; WC_PERSISTENT=w78tdcYGEYfbxl1%2BQgFnNem5g1fyo0VjxFMf4FL6DSo%3D%3B2025-05-09+15%3A12%3A42.15_1746792762150-814288_0; AKA_A2=A; JSESSIONID=0000qP7bMUJSN80vfnA5ERQuHn6:-1; REFERRER=https%3A%2F%2Fwww.kotsovolos.gr%2Fstore%2Fioannina-spot',
    }

    params = {
        "radius": "1000",
        "maxItems": "150",
        "siteLevelStoreSearch": "false",
    }

    def start_requests(self):

        full_url = self.main_endpoint + urlencode(self.params)
        yield scrapy.Request(
            url=full_url,
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse,
        )

    def parse(self, response):

        data = json.loads(response.text).get("PhysicalStore")

        for store in data:

            yield {
                "addr_full": "".join(store.get("addressLine")),
                "brand": "Kotsovolos",
                "city": store.get("city"),
                "country": "Greece",
                "extras": {
                    "brand": "Kotsovolos",
                    "fascia": "Kosovolos",
                    "category": "Retail",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
                "name": f"Kotsovolos {store.get("Description")[0].get("displayStoreName")}",
                "opening_hours": self.parse_opening_hours(store.get("Attribute")),
                "phone": (
                    store.get("telephone1").replace(" ", "")
                    if store.get("telephone1")
                    else None
                ),
                "postcode": (
                    re.sub(r"\s+", "", store.get("postalCode"))
                    if store.get("postalCode")
                    else store.get("postalCode")
                ),
                "ref": store.get("uniqueID"),
                "state": None,
                "website": f"https://www.kotsovolos.gr/store/{store.get("x_Keyword")}",
            }

    def parse_opening_hours(self, opening_hour):

        hour = {}

        opening_hour_dicts = [
            op_hr for op_hr in opening_hour if op_hr.get("name").startswith("WH")
        ]

        days_mapping = {
            "Δευτέρα": "Mon",
            "Τρίτη": "Tue",
            "Τετάρτη": "Wed",
            "Πέμπτη": "Thu",
            "Παρασκευή": "Fri",
            "Σάββατο": "Sat",
            "Κυριακή": "Sun",
        }

        for wk_hour in opening_hour_dicts:
            hour[days_mapping.get(wk_hour.get("displayName"))] = wk_hour.get("value")

        return {"opening_hours": hour}
