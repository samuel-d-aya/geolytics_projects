import re
import urllib.parse
import datetime
import scrapy


class LeroymerlinSpider(scrapy.Spider):
    name = "leroymerlin"
    allowed_domains = ["www.leroymerlin.gr"]
    start_urls = ["https://www.leroymerlin.gr/gr/stores"]

    def start_requests(self):  # type: ignore
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_store_url)  # type: ignore

    def parse_store_url(self, response):  # type: ignore
        stores_url = response.css(".storesButton > a::attr(href)").getall()  # type: ignore

        for url in stores_url:  # type: ignore
            yield response.follow(url=url, callback=self.parse)  # type: ignore

    def parse(self, response):  # type: ignore

        lat_lon = self.parse_lat_lon(response.css(".storeMap > ::attr(href)").get())  # type: ignore

        yield {
            "addr_full": re.sub(
                r"\s+", " ", response.css(".storeAdress::text").get()  # type: ignore
            ),
            "brand": "Leroy Merlin",
            "city": re.sub(
                r"\s+", " ", response.css(".storeAdress::text").get()  # type: ignore
            ).split()[-1],
            "country": "Greece",
            "extras": {
                "brand": "Leroy Merlin",
                "fascia": "Leroy Merlin",
                "category": "Retail",
                "edit_date": str(datetime.datetime.now().date()),  # type: ignore
                "lat_lon_source": "Third Party",
            },
            "lat": lat_lon[0],
            "lon": lat_lon[1],
            "name": f"Leroy Merlin {response.css(".storeHeaderTitle::text").get()}",  # type: ignore
            "opening_hours": self.parse_opening_hours(
                response.css("h5 > strong::text").getall()[:3]
            ),
            "phone": re.sub(r"\s+", "", response.css(".storeTel::text").get()).split(".:")[-1],  # type: ignore
            "postcode": None,
            "ref": response.url.split("id_store=")[-1].split("?")[0],  # type: ignore
            "state": None,
            "website": response.url,  # type: ignore
        }

    def parse_lat_lon(self, url):  # type: ignore
        decoded_url = urllib.parse.unquote(url)  # type: ignore
        match = re.search(r"([+-]?\d+\.\d+),([+-]?\d+\.\d+)", decoded_url)
        if match:
            lat, lon = match.groups()
            return float(lat), float(lon)
        return None, None

    def parse_opening_hours(self, text_lines):  # type: ignore

        result = {}

        # Day mappings (Greek abbreviations to English three-letter codes)
        day_mappings = {
            "Δευ": "Mon",
            "Τρι": "Tue",
            "Τετ": "Wed",
            "Πεμ": "Thu",
            "Παρ": "Fri",
            "Σάβ": "Sat",
            "Κυρ": "Sun",
        }

        for line in text_lines:

            if ":" not in line or "-" not in line:
                continue

            day_part = line.split(":")[0].strip()
            time_part = ":".join(line.split(":")[1:]).strip()

            if ".-" in day_part or ".-" in day_part or "-" in day_part:

                if ".-" in day_part:
                    start_day, end_day = day_part.split(".-")
                elif "-" in day_part:
                    start_day, end_day = day_part.split("-")
                else:
                    start_day, end_day = day_part.split(".")
                    end_day = end_day.lstrip("-")

                start_day = start_day.strip().rstrip(".")
                end_day = end_day.strip().rstrip(".")

                start_code = None
                end_code = None

                for greek_prefix, eng_code in day_mappings.items():
                    if start_day.startswith(greek_prefix):
                        start_code = eng_code
                    if end_day.startswith(greek_prefix):
                        end_code = eng_code

                if start_code and end_code:

                    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    start_idx = day_order.index(start_code)
                    end_idx = day_order.index(end_code)

                    time_info = time_part.strip()

                    time_parts = time_info.split("-")
                    if len(time_parts) == 2:
                        opening, closing = time_parts[0].strip(), time_parts[1].strip()

                        if ":" in opening and len(opening.split(":")[0]) == 1:
                            opening = f"0{opening}"
                        if ":" in closing and len(closing.split(":")[0]) == 1:
                            closing = f"0{closing}"

                        time_range = f"{opening} - {closing}"

                        for i in range(start_idx, end_idx + 1):
                            result[day_order[i]] = time_range

            else:
                day_part = day_part.rstrip(".")

                for greek_prefix, eng_code in day_mappings.items():
                    if day_part.startswith(greek_prefix):

                        time_info = time_part.strip()

                        time_parts = time_info.split("-")
                        if len(time_parts) == 2:
                            opening, closing = (
                                time_parts[0].strip(),
                                time_parts[1].strip(),
                            )

                            if ":" in opening and len(opening.split(":")[0]) == 1:
                                opening = f"0{opening}"
                            if ":" in closing and len(closing.split(":")[0]) == 1:
                                closing = f"0{closing}"

                            time_range = f"{opening} - {closing}"

                            result[eng_code] = time_range

        return {"opening_hours": result}
