import re
import requests
import datetime
import scrapy


class SmarketSpider(scrapy.Spider):
    name = "smarket"
    allowed_domains = ["www.smarket.co.kr"]
    start_urls = ["https://www.smarket.co.kr/board/list.php?page="]
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

    def start_requests(self):
        for page in range(1, 8):
            url = f"{self.start_urls[0]}{page}&bdId=offline"
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        stores = response.css(".board_list_gallery > ul > li")
        print(f"\n\nFound {len(stores)} stores on page {response.url}\n\n")
        for store in stores:

            addr = (
                store.css(".board_cont > p:nth-child(1) > font span::text").get()
                or store.css(".board_cont > p:nth-child(1) > font::text").get()
                or store.css(".board_cont > p:nth-child(1)::text").get()
            )

            phone = (
                store.css(".board_cont > p:nth-child(2) > font span::text").get()
                or store.css(".board_cont > p:nth-child(2) > font::text").get()
                or store.css(".board_cont > p:nth-child(2)::text").get()
                if (
                    store.css(".board_cont > p:nth-child(2) > font span::text").get()
                    or store.css(".board_cont > p:nth-child(2) > font::text").get()
                    or store.css(".board_cont > p:nth-child(2)::text").get()
                ).startswith("T")
                else store.css(".board_cont > p:nth-child(3) > font span::text").get()
                or store.css(".board_cont > p:nth-child(3) > font::text").get()
                or store.css(".board_cont > p:nth-child(3)::text").get()
            ).replace("T. ", "")

            op_hr = (
                store.css(".board_cont > p > font > span::text").getall()[2:]
                or store.css(".board_cont > p::text").getall()[2:]
                or store.css(".board_cont > p > font::text").getall()[2:]
                if (
                    store.css(".board_cont > p:nth-child(2) > font span::text").get()
                    or store.css(".board_cont > p:nth-child(2) > font::text").get()
                    or store.css(".board_cont > p:nth-child(2)::text").get()
                ).startswith("T")
                else store.css(".board_cont > p > font > span::text").getall()[3:]
                or store.css(".board_cont > p::text").getall()[3:]
                or store.css(".board_cont > p > font::text").getall()[3:]
            )

            print(f"\n\n{op_hr}\n\n")

            print(
                f"\n\nStore Name: { re.sub(
                    r"\s+", " ", store.css(".board_tit > strong::text").get()
                ).strip()}\n\n"
            )

            print(f"\n\nAddress: {addr}\n\n")
            self.logger.info(f"\n\n{addr}\n\n")
            print(
                f"\n\n Telephone: {store.css('.board_cont > p:nth-child(2)::text').get()}\n\n"
            )

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
            self.logger.info(f"\n\n{data}\n\n")

            if not data.get("documents"):
                location = self.geocode_address(
                    addr, "AIzaSyAgZy2MBG8jU1rOOPBWx4jN7y85rK23I7w"
                )
                lat = location.get("latitude")
                lon = location.get("longitude")
            else:
                lat = data.get("documents")[0].get("y")
                lon = data.get("documents")[0].get("x")

            yield {
                "addr_full": addr,
                "brand": "Smarket",
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
                    "brand": "Smarket",
                    "fascia": "Smarket",
                    "category": "Retail",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Google",
                },
                "lat": lat,
                "lon": lon,
                "name": re.sub(
                    r"\s+", " ", store.css(".board_tit > strong::text").get()
                ).strip(),
                "opening_hours": self.parse_opening_hours(" ".join(op_hr)),
                "phone": re.sub(r"T.|\s+|xa", "", phone),
                "postcode": (
                    (
                        data.get("documents")[0].get("road_address", {}).get("zone_no")
                        if data.get("documents")[0].get("road_address", {})
                        else None
                    )
                    if data.get("documents")
                    else None
                ),
                "ref": f"{lat}-{lon}",
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

    def parse_opening_hours(self, hours_str):

        result = {
            "Mon": "00:00 - 23:59",
            "Tue": "00:00 - 23:59",
            "Wed": "00:00 - 23:59",
            "Thu": "00:00 - 23:59",
            "Fri": "00:00 - 23:59",
            "Sat": "Closed",
            "Sun": "Closed",
        }

        def parse_time(time_str):

            if any(
                char in time_str
                for char in [
                    "①",
                    "②",
                    "③",
                    "④",
                    "⑤",
                    "⑥",
                    "⑦",
                    "일",
                    "월",
                    "화",
                    "수",
                    "목",
                    "금",
                    "토",
                ]
            ):

                parts = time_str.split("/")
                if len(parts) == 2:
                    time_part = parts[1].strip()
                    if "~" in time_part:
                        times = time_part.split("~")
                        opening_time = times[0].strip()
                        closing_time = times[1].strip()

                        if ":" in opening_time:
                            opening_hour = int(opening_time.split(":")[0])
                            opening_minute = int(opening_time.split(":")[1])
                        else:
                            opening_hour = int(opening_time)
                            opening_minute = 0

                        if ":" in closing_time:
                            closing_hour = int(closing_time.split(":")[0])
                            closing_minute = int(closing_time.split(":")[1])
                        else:
                            closing_hour = int(closing_time)
                            closing_minute = 0

                        return f"{opening_hour:02d}:{opening_minute:02d} - {closing_hour:02d}:{closing_minute:02d}"

                return ""

            if "~" in time_str:
                times = time_str.split("~")
                opening_time = times[0].strip()
                closing_time = times[1].strip()

                try:

                    if "AM" in opening_time or "PM" in opening_time:
                        opening_hour = int(
                            "".join(
                                c
                                for c in opening_time.replace("AM", "").replace(
                                    "PM", ""
                                )
                                if c.isdigit() or c == ":"
                            ).split(":")[0]
                        )
                        if "PM" in opening_time and opening_hour < 12:
                            opening_hour += 12
                        opening_minute = 0
                        if ":" in opening_time:
                            minute_part = "".join(
                                c
                                for c in opening_time.replace("AM", "").replace(
                                    "PM", ""
                                )
                                if c.isdigit() or c == ":"
                            ).split(":")
                            if len(minute_part) > 1:
                                opening_minute = int(minute_part[1])
                    else:

                        if ":" in opening_time:
                            opening_hour = int(opening_time.split(":")[0])
                            opening_minute = int(opening_time.split(":")[1])
                        else:
                            opening_hour = int(opening_time)
                            opening_minute = 0

                    if "AM" in closing_time or "PM" in closing_time:
                        closing_hour = int(
                            "".join(
                                c
                                for c in closing_time.replace("AM", "").replace(
                                    "PM", ""
                                )
                                if c.isdigit() or c == ":"
                            ).split(":")[0]
                        )
                        if "PM" in closing_time and closing_hour < 12:
                            closing_hour += 12
                        closing_minute = 0
                        if ":" in closing_time:
                            minute_part = "".join(
                                c
                                for c in closing_time.replace("AM", "").replace(
                                    "PM", ""
                                )
                                if c.isdigit() or c == ":"
                            ).split(":")
                            if len(minute_part) > 1:
                                closing_minute = int(minute_part[1])
                    else:

                        if ":" in closing_time:
                            closing_hour = int(closing_time.split(":")[0])
                            closing_minute = int(closing_time.split(":")[1])
                        else:
                            closing_hour = int(closing_time)
                            closing_minute = 0

                    return f"{opening_hour:02d}:{opening_minute:02d} - {closing_hour:02d}:{closing_minute:02d}"
                except (ValueError, IndexError):
                    return ""

            return ""

        sections = hours_str.split("운영")
        has_specific_days = False

        if (
            "①" in hours_str
            or "②" in hours_str
            or "③" in hours_str
            or "④" in hours_str
            or "⑤" in hours_str
            or "⑥" in hours_str
            or "⑦" in hours_str
        ):

            if "④" in hours_str and "일" in hours_str:

                sun_part = [
                    part
                    for part in hours_str.split("\xa0")
                    if "④" in part and "일" in part
                ]
                if sun_part:
                    sun_time = parse_time(sun_part[0])
                    if sun_time:
                        result["Sun"] = sun_time
                        has_specific_days = True

            if has_specific_days:
                return result

        for section in sections:
            if not section.strip():
                continue

            section = section.strip()
            if section.startswith(":"):
                section = section[1:].strip()

            if "(" in section and ")" in section:
                time_part = section[: section.find("(")].strip()
                day_info = section[section.find("(") + 1 : section.find(")")].strip()
                formatted_time = parse_time(time_part)

                if "휴무" in day_info:

                    default_time = formatted_time
                    for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                        result[day] = default_time

                    if "일요일" in day_info:
                        if "2,4주차" in day_info:

                            result["Sun"] = formatted_time
                        else:
                            result["Sun"] = "Closed"

                    has_specific_days = True
                elif day_info == "평일":
                    result["Mon"] = formatted_time
                    result["Tue"] = formatted_time
                    result["Wed"] = formatted_time
                    result["Thu"] = formatted_time
                    result["Fri"] = formatted_time
                    has_specific_days = True
                elif day_info == "주말":
                    result["Sat"] = formatted_time
                    result["Sun"] = formatted_time
                    has_specific_days = True
            else:

                formatted_time = parse_time(section)
                if formatted_time and not has_specific_days:

                    for day in result:
                        result[day] = formatted_time

        return {"opening_hours": result}

    def geocode_address(self, address, api_key):
        params = {"address": address, "key": api_key}
        response = requests.get(self.google_map_api, params=params)
        data = response.json()

        if data["status"] != "OK":
            raise Exception(f"Geocoding error: {data['status']}")

        result = data["results"][0]
        lat = result["geometry"]["location"]["lat"]
        lng = result["geometry"]["location"]["lng"]

        return {
            "latitude": lat,
            "longitude": lng,
        }
