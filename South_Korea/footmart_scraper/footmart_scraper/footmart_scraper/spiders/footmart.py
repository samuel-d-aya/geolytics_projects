import requests
import datetime
import scrapy
from geopy.geocoders import Nominatim


class FootmartSpider(scrapy.Spider):
    name = "footmart"
    allowed_domains = ["www.foot-mart.co.kr"]
    start_urls = [
        "https://www.foot-mart.co.kr/main/html.php?htmid=service/store_guide.html&__gd5_skin_preview=NTgwNTI4XnxeMTc1LjEyNC4xNTQuNDVefF5mcm9udF58XnJfamEwNl58XjE2NjUxMDI2NDY="
    ]
    geolocator = Nominatim(user_agent=name)

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "KakaoAK abd31b6fe9130f34beb0779b5e7fcb00",
        "ka": "sdk/4.4.19 os/javascript lang/en-US device/Win32 origin/https%3A%2F%2Fwww.shoemarker.co.kr",
        "origin": "https://www.shoemarker.co.kr",
        "priority": "u=1, i",
        "referer": "https://www.shoemarker.co.kr/",
        "sec-ch-ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_store_url)

    def parse_store_url(self, response):

        stores = response.css("table > tbody > tr")
        print(f"\n\n{len(stores)}")

        for store in stores:

            if not store.css("td.tg-ve35::text").get():
                continue

            print(f"\n\n{store.css("td.tg-i3ot::text").getall()}\n\n")
            print(f"\n\n{store.css("td.tg-ve35::text").get()}\n\n")

            store_name = store.css("td.tg-ve35::text").get()
            store_address = store.css("td.tg-i3ot::text").getall()[0]
            store_number = (
                store.css("td.tg-i3ot::text").getall()[1]
                if len(store.css("td.tg-i3ot::text").getall()) > 1
                else None
            )

            store_url = store.css("td.tg-wo29 > a::attr(href)").get()

            yield response.follow(
                url=store_url,
                meta={"name": store_name, "addr": store_address, "num": store_number},
                callback=self.parse_more_details,
            )

    def parse_more_details(self, response):

        op_hr = (
            response.xpath("//p[contains(text(), '매장영업시간')]/text()")
            .get()
            .split("매장영업시간 : ")[-1]
            .replace("~", "-")
            if response.xpath("//p[contains(text(), '매장영업시간')]/text()").get()
            else "00:00 - 23:59"
        )

        params = {
            "query": response.meta.get("addr"),
            "page": 1,
            "size": 10,
        }

        output = requests.get(
            "https://dapi.kakao.com/v2/local/search/address.json",
            params=params,
            headers=self.headers,
        )

        data = output.json()
        self.logger.info(f"\n\n{data}\n\n")

        if not data.get("documents"):
            location = self.geolocator.geocode("addr")
            lat = location.latitude
            lon = location.longitude
        else:
            lat = data.get("documents")[0].get("y")
            lon = data.get("documents")[0].get("x")

        yield {
            "addr_full": response.meta.get("addr"),
            "brand": "FootMart",
            "city": (
                (
                    data.get("documents")[0]
                    .get("address", {})
                    .get("region_2depth_name")
                    if data.get("documents")[0].get("address", {})
                    else (
                        data.get("documents")[0]
                        .get("road_address", {})
                        .get("region_2depth_name")
                    )
                )
                if data.get("documents")
                else None
            ),
            "country": "South Korea",
            "extras": {
                "brand": "Footmart",
                "fascia": "Footmart",
                "category": "Retail",
                "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                "lat_lon_source": "Third Party",
            },
            "lat": lat,
            "lon": lon,
            "name": response.meta.get("name"),
            "opening_hours": {
                "opening_hours": {
                    "Mon": op_hr,
                    "Tue": op_hr,
                    "Wed": op_hr,
                    "Thu": op_hr,
                    "Fri": op_hr,
                    "Sat": op_hr,
                    "Sun": op_hr,
                }
            },
            "phone": response.meta.get("name"),
            "postcode": (
                (
                    data.get("documents")[0].get("road_address", {}).get("zone_no")
                    if data.get("documents")[0].get("road_address", {})
                    else None
                )
                if data.get("documents")
                else None
            ),
            "ref": response.url.split("=")[-1],
            "state": (
                (
                    data.get("documents")[0]
                    .get("address", {})
                    .get("region_1depth_name")
                    if data.get("documents")[0].get("address", {})
                    else data.get("documents")[0]
                    .get("road_address", {})
                    .get("region_1depth_name")
                )
                if data.get("documents")
                else None
            ),
            "website": response.url,
        }
