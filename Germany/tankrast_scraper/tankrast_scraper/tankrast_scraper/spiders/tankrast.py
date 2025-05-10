import datetime
import re
import requests
import scrapy


class TankrastSpider(scrapy.Spider):
    name = "tankrast"
    allowed_domains = [
        "www.raststaetten.de",
        "www.serways-hotels.de",
        "rosis-autohof.de",
        "www.raststaetten-hotels.de",
    ]
    start_urls_map = {
        "parse_raststaetten_url": "https://www.raststaetten.de/alle-standorte/",
        "parse_serways_url": "https://www.serways-hotels.de/",
        "parse_rosis_url": "https://rosis-autohof.de/",
    }
    google_map_api = "https://maps.googleapis.com/maps/api/geocode/json"

    def start_requests(self):
        for parse_func, url in self.start_urls_map.items():
            callback = getattr(self, parse_func)
            yield scrapy.Request(url=url, callback=callback)

    def parse_raststaetten_url(self, response):

        stores_url = response.css(
            ".locations-list .container .location-info-card > a::attr(href)"
        ).getall()

        for url in stores_url:
            yield response.follow(url=url, callback=self.parse_raststaetten_detail)

    def parse_raststaetten_detail(self, response):

        self.logger.info(
            f"\n\n{response.css(".location-headline + a::attr(href)").get()}\n\n"
        )

        coord = self.extract_lat_lon_ras(
            response.css(".location-headline + a::attr(href)").get()
        )

        addr = addr = (
            response.css("div.headline-type-4 + p::text").getall()
            if [
                item.startswith(" Telefon") or item.startswith(" An der")
                for item in response.css("div.headline-type-4 + p::text").getall()
            ][0]
            else response.css("div.headline-type-4 ~ p::text").getall()
        )

        ph_lst = [item for item in addr if item.startswith(" Telefon")]
        addr_full = (
            f"{response.css("h1.has-subtitle::text").getall()[1]}{' '.join([
                next(
                    (p.strip() for p in addr if "An der" in p), None
                    ),
                next(
                (
                    line.strip()
                    for line in addr
                    if re.search(r"\d{5}\s+[A-Za-zäöüÄÖÜß]+", line)
                ),
                None,
            ),])}",
        )[0]

        yield {
            "addr_full": addr_full,
            "brand": "Tank & Rast",
            "city": next(
                (
                    line.strip()
                    for line in addr
                    if re.search(r"\d{5}\s+[A-Za-zäöüÄÖÜß]+", line)
                ),
                None,
            ).split()[1],
            "country": "Germany",
            "extras": {
                "brand": "Tank & Rast",
                "fascia": "Motorway Service Station",
                "category": "Other",
                "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                "lat_lon_source": "Google",
            },
            "lat": coord[0],
            "lon": coord[1],
            "name": " ".join(response.css("h1.has-subtitle::text").getall()),
            "opening_hours": self.parse_opening_hours_r(addr),
            "phone": ph_lst[0].split(": ")[1] if ph_lst else None,
            "postcode": next(
                (
                    line.strip()
                    for line in addr
                    if re.search(r"\d{5}\s+[A-Za-zäöüÄÖÜß]+", line)
                ),
                None,
            ).split()[1],
            "ref": f"{coord[0]}-{coord[1]}",
            "state": response.css("h1.has-subtitle::text").getall()[1],
            "website": response.url,
        }

    def parse_serways_url(self, response):

        store_url = response.css(
            ".map-popover-wrap > .map-popover > a::attr(href)"
        ).getall()

        for url in store_url:
            furl = response.urljoin(url)
            yield response.follow(
                url=furl,
                callback=self.parse_serways_detail,
            )

    def parse_serways_detail(self, response):

        store = response.css(".hotel-location")

        yield {
            "addr_full": " ".join(
                response.css(".address p:nth-child(2)::text").getall()
            ),
            "brand": "Tank & Rast",
            "city": response.css(".address p:nth-child(2)::text")
            .getall()[-1]
            .split()[-1],
            "country": "Germany",
            "extras": {
                "brand": "Tank & Rast",
                "fascia": "Serways Hotel",
                "category": "Leisure",
                "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                "lat_lon_source": "Google",
            },
            "lat": store.css(".map > div::attr(data-latitude)").get(),
            "lon": store.css(".map > div::attr(data-longitude)").get(),
            "name": f"Serways Hotel {re.sub(r"\s+", " ", response.css(".stage__headline::text").get())}",
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
            "phone": store.css("table td:nth-child(2) > a::text").get(),
            "postcode": response.css(".address p:nth-child(2)::text")
            .getall()[-1]
            .split()[0],
            "ref": response.css("body::attr(id)").get(),
            "state": re.sub(r"\s+", "", response.css(".stage__headline::text").get()),
            "website": response.url,
        }

    def parse_rosis_url(self, response):

        stores_url = response.css(".sub-menu > li > a::attr(href)").getall()

        for url in stores_url:
            furl = response.urljoin(url)
            yield response.follow(url=furl, callback=self.parse_rosis_detail)

    def parse_rosis_detail(self, response):

        self.logger.info(
            f"\n\n{response.css(
                ".elementor-element .elementor-widget-container .elementor-button-link::attr(href)"
            ).get()}\n\n"
        )

        coord = self.extract_lat_lon_ros(
            response.css(
                ".elementor-element .elementor-widget-container .elementor-button-link::attr(href)"
            ).get()
        )

        addr_list = [
            re.sub(r"\s+", " ", item)
            for item in response.css(".elementor-widget-container > p")[0]
            .css("::text")
            .getall()
        ]

        if coord:
            lat = coord[0]
            lon = coord[1]

        else:
            coord = self.geocode_address(
                " ".join(addr_list[:-1]), "AIzaSyAgZy2MBG8jU1rOOPBWx4jN7y85rK23I7w"
            )
            lat = coord.get("latitude")
            lon = coord.get("longitude")

        self.logger.info(f"\n\n{" ".join(addr_list[:-1])}\n\n")

        yield {
            "addr_full": " ".join(addr_list[:-1]),
            "brand": "Tank & Rast",
            "city": addr_list[1].split(maxsplit=1)[1],
            "country": "Germany",
            "extras": {
                "brand": "Tank & Rast",
                "fascia": "Rosi's Autohof",
                "category": "Food and Beverage",
                "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                "lat_lon_source": "Google",
            },
            "lat": lat,
            "lon": lon,
            "name": re.sub(
                r"\s+", "", response.css("h1.elementor-heading-title::text").get()
            ),
            "opening_hours": self.parse_opening_hours(
                response.css("table > tbody > tr:last-child >td:last-child::text").get()
            ),
            "phone": (
                addr_list[-1].split(": ")[1].replace(" ", "")
                if len(addr_list[-1].split(": ")) > 1
                else addr_list[-1].replace(" ", "")
            ),
            "postcode": addr_list[1].split(maxsplit=1)[0],
            "ref": f"{lat}{lon}",
            "state": None,
            "website": response.url,
        }

    def extract_lat_lon_ros(self, url):
        match = re.search(r"@([-.\d]+),([-.\d]+)", url)
        if match:
            lat, lon = match.groups()
            return float(lat), float(lon)
        return None

    def extract_lat_lon_ras(self, url):
        coords_pattern = r"(-?\d+\.\d+),(-?\d+\.\d+)"
        match = re.search(coords_pattern, url)

        if match:
            return float(match.group(1)), float(match.group(2))

        # If no pattern matched, return None
        return None, None

    def parse_opening_hours(self, opening_hour):
        day_map = {
            "Mo": "Mon",
            "Di": "Tue",
            "Mi": "Wed",
            "Do": "Thu",
            "Fr": "Fri",
            "Sa": "Sat",
            "So": "Sun",
        }

        result = {day: "" for day in day_map.values()}

        groups = [g.strip() for g in opening_hour.split(",")]

        for group in groups:

            day_part = re.search(r"([A-Za-z]{2})(?:-([A-Za-z]{2}))?", group)
            time_part = re.search(
                r"von\s+(\d{2}:\d{2})\s+Uhr\s+bis\s+(\d{2}:\d{2})", group
            )

            if not day_part or not time_part:
                continue

            start_day = day_map.get(day_part.group(1))
            end_day = day_map.get(day_part.group(2)) if day_part.group(2) else start_day
            open_time, close_time = time_part.groups()

            days = list(day_map.values())
            start_index = days.index(start_day)
            end_index = days.index(end_day) + 1
            day_range = days[start_index:end_index]

            for day in day_range:
                result[day] = f"{open_time} - {close_time}"

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

    def parse_opening_hours_r(self, paragraphs):
        # Dictionary for day abbreviation mapping and result storage
        day_mapping = {
            "Mo": "Mon",
            "Di": "Tue",
            "Mi": "Wed",
            "Do": "Thu",
            "Fr": "Fri",
            "Sa": "Sat",
            "So": "Sun",
            # English abbreviations
            "Mon": "Mon",
            "Tue": "Tue",
            "Wed": "Wed",
            "Thu": "Thu",
            "Fri": "Fri",
            "Sat": "Sat",
            "Sun": "Sun",
        }

        # Dictionary to store the results
        result = {}

        # Find paragraphs that look like opening hours
        hour_patterns = [p for p in paragraphs if re.search(r"\d{1,2}:\d{2}", p)]

        for text in hour_patterns:
            # Extract day range and time
            match = re.search(
                r"([A-Za-z]{2})-([A-Za-z]{2}):\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})",
                text,
            )
            if match:
                start_day, end_day, start_time, end_time = match.groups()

                # Convert day abbreviations to standardized format
                start_day = day_mapping.get(start_day, start_day)
                end_day = day_mapping.get(end_day, end_day)

                # Get the list of days in order
                all_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                start_idx = all_days.index(start_day)
                end_idx = all_days.index(end_day)

                # Handle cases where end day is before start day in the week
                if end_idx < start_idx:
                    end_idx += 7

                # Assign hours to each day in the range
                for i in range(start_idx, end_idx + 1):
                    day = all_days[i % 7]
                    result[day] = f"{start_time} - {end_time}"

        # Special case handling (could be expanded)
        for text in hour_patterns:
            if "Donnerstags bis 24 Uhr" in text:
                result["Thu"] = result.get("Thu", "").split(" - ")[0] + " - 24:00"

        # Fill in any missing days with closed status
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            if day not in result:
                result[day] = "00:00-23:59"

        return result
