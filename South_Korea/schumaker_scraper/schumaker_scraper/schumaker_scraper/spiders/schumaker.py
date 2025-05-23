import datetime
import json
import requests
import re
import scrapy
from scrapy.selector import Selector
from scrapy.spidermiddlewares.httperror import HttpError


class SchumakerSpider(scrapy.Spider):
    name = "schumaker"
    allowed_domains = ["www.shoemarker.co.kr"]
    # start_urls = ["https://www.shoemarker.co.kr/ASP/Customer/Ajax/StoreView.asp?Page="]
    start_urls = ["https://www.shoemarker.co.kr/ASP/Customer/Ajax/StoreView.asp?Page="]
    address_endpoint = "https://dapi.kakao.com/v2/local/search/address.json"
    google_map_api = "https://maps.googleapis.com/maps/api/geocode/json"

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

    theaders = {
        "Accept": "text/plain, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "HDSUBSTORE1": "akc1UUtEYTgxVWtHVHAwTW8yTnl2OXV2VmtNOW9hMGQ=",
        "Origin": "https://www.shoemarker.co.kr",
        "Referer": "https://www.shoemarker.co.kr/ASP/Customer/Store.asp",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        # "Cookie": "GuestInfo=ddqAab%2FqlRryH%2FwouEX4MIKIF0vEObsc3O0ixyF2YDM%3D; USESSIONID=lHcq0pH9gzMtkZ8ELYJWIQ%3D%3D; UCARTID=lHcq0pH9gzMtkZ8ELYJWIQ%3D%3D; ASPSESSIONIDAAQQRBST=HMGCFPBDKIOHNHDACLNMKLCG; ASPSESSIONIDCSTCRBRT=BPNBBCBDMDACNGMDLIIEIBIA; shoemarker.co.kr-crema_device_token=Z8rsQqxlqU8pQXlPr0zYwbo2H6oHgdI9; _CHAT_DEVICEID=1967CEE0715; CUR_STAMP=1745852696340; _NB_MHS=1-1745852701; ASPSESSIONIDCASSRDRS=EKIFALODBJNDKAPGBJGJMPHK; ASPSESSIONIDAQRBSBRS=ACMGMNNDEPJGAPNDFANBDKGK; CKSUBSTORE1=akc1UUtEYTgxVWtHVHAwTW8yTnl2OXV2VmtNOW9hMGQ%3D",
    }

    cookies = {
        "GuestInfo": "ddqAab%2FqlRryH%2FwouEX4MIKIF0vEObsc3O0ixyF2YDM%3D",
        "USESSIONID": "lHcq0pH9gzMtkZ8ELYJWIQ%3D%3D",
        "UCARTID": "lHcq0pH9gzMtkZ8ELYJWIQ%3D%3D",
        "ASPSESSIONIDAAQQRBST": "HMGCFPBDKIOHNHDACLNMKLCG",
        "ASPSESSIONIDCSTCRBRT": "BPNBBCBDMDACNGMDLIIEIBIA",
        "shoemarker.co.kr-crema_device_token": "Z8rsQqxlqU8pQXlPr0zYwbo2H6oHgdI9",
        "_CHAT_DEVICEID": "1967CEE0715",
        "CUR_STAMP": "1745852696340",
        "_NB_MHS": "1-1745852701",
        "ASPSESSIONIDCASSRDRS": "EKIFALODBJNDKAPGBJGJMPHK",
        "ASPSESSIONIDAQRBSBRS": "ACMGMNNDEPJGAPNDFANBDKGK",
        "CKSUBSTORE1": "akc1UUtEYTgxVWtHVHAwTW8yTnl2OXV2VmtNOW9hMGQ%3D",
    }

    data = {
        "ChannelNM": "",
        "Area": "",
        "AreaNM": "지역전체",
        "Keyword": "",
        "pickup-location": "on",
    }

    def start_requests(self):
        for page in range(1, 23):
            url = f"{self.start_urls[0]}{page}"

            yield scrapy.Request(
                url=url,
                method="POST",
                headers=self.theaders,
                body=json.dumps(self.data),
                cookies=self.cookies,
                callback=self.parse_text,
            )

    def parse_text(self, response):

        scrapy_response = Selector(text=response.text)
        stores = scrapy_response.css(".radio-pickup")
        for store in stores:
            addr = store.css(".shop-addr::text").get()

            self.logger.info("\n\n{addr}\n\n")

            params = {
                "query": addr,
                "page": 1,
                "size": 10,
            }

            output = requests.get(
                "https://dapi.kakao.com/v2/local/search/address.json",
                params=params,
                headers=self.headers,
            )

            data = output.json()

            if not data.get("documents"):

                google_geocode = self.geocode_address(
                    addr, "AIzaSyAgZy2MBG8jU1rOOPBWx4jN7y85rK23I7w"
                )

            op_hr = (
                store.css(".shop-tel::text")
                .get()
                .split("/")[1]
                .strip()
                .replace("~", "-")
                if len(store.css(".shop-tel::text").get().split("/")) > 1
                else "00:00-23:59"
            )

            yield {
                "addr_full": store.css(".shop-addr::text").get(),
                "brand": "Shoemarker",
                "city": (
                    data.get("documents")[0].get("address").get("region_2depth_name")
                    if data.get("documents")
                    else google_geocode.get("city")
                ),
                "country": "South Korea",
                "extras": {
                    "brand": "Shoemarker",
                    "fascia": "Shoemarker",
                    "category": "Retail",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Third Party",
                },
                "lat": (
                    data.get("documents")[0].get("y")
                    if data.get("documents")
                    else google_geocode.get("latitude")
                ),
                "lon": (
                    data.get("documents")[0].get("x")
                    if data.get("documents")
                    else google_geocode.get("longitude")
                ),
                "name": re.sub(r"\s+", "", store.css(".shop-name::text").get()),
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
                "phone": store.css(".shop-tel::text").get().split("/")[0].strip(),
                "postcode": (
                    data.get("documents")[0].get("road_address").get("zone_no")
                    if data.get("documents")
                    else google_geocode.get("zipcode")
                ),
                "ref": f"{data.get('documents')[0].get('y') if data.get("documents")
                    else google_geocode.get("latitude")}-{data.get('documents')[0].get('x') if data.get("documents")
                    else google_geocode.get("longitude")}",
                "state": (
                    data.get("documents")[0].get("address").get("region_1depth_name")
                    if data.get("documents")
                    else google_geocode.get("state")
                ),
                "website": self.start_urls[0],
            }

    def errback(self, failure):
        self.logger.error(repr(failure))
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(
                f"HTTP Error on {response.url} - Status: {response.status}"
            )

    def geocode_address(self, address, api_key):
        params = {"address": address, "key": api_key}
        response = requests.get(self.google_map_api, params=params)
        data = response.json()

        if data["status"] != "OK":
            raise Exception(f"Geocoding error: {data['status']}")

        result = data["results"][0]
        components = result["address_components"]
        lat = result["geometry"]["location"]["lat"]
        lng = result["geometry"]["location"]["lng"]

        city = state = district = postal_code = None

        for comp in components:
            if "administrative_area_level_1" in comp["types"]:
                state = comp["long_name"]
            elif (
                "administrative_area_level_2" in comp["types"]
                or "locality" in comp["types"]
            ):
                city = comp["long_name"]
            elif "sublocality_level_1" in comp["types"]:
                district = comp["long_name"]
            elif "postal_code" in comp["types"]:
                postal_code = comp["long_name"]

        return {
            "address": address,
            "state": state or district,
            "city": city,
            "zipcode": postal_code,
            "latitude": lat,
            "longitude": lng,
        }
