import scrapy
import json
import datetime
import re
import html


class HermesSpider(scrapy.Spider):
    name = "hermes"
    allowed_domains = ["www.hermes.com", "bck.hermes.com"]
    start_urls = ["https://bck.hermes.com/stores?lang=en&locale=us_en"]

    def start_requests(self):
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.hermes.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "X-Hermes-Locale": "us_en",
            "Accept-Language": "en-US,en;q=0.6",
            "Origin": "https://www.hermes.com",
            "Sec-Ch-Ua": '"Chromium";v="134", "Not=A?Brand";v="24", "Brave";v="134"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Sec-Gpc": "1",
        }

        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                headers=headers,
                meta={"dont_merge_cookies": True},
                callback=self.parse,
            )

    def parse(self, response):
        data = json.loads(response.text)

        for store in data.get("shops", []):
            if store.get("country") == "Japan":
                yield {
                    "addr_full": store.get("streetAddress1"),
                    "brand": "Hermes",
                    "city": store.get("city"),
                    "country": store.get("country"),
                    "extras": {
                        "brand": "Hermes",
                        "fascia": "",
                        "category": "Fashion",
                        "edit_date": datetime.datetime.now().strftime('%Y%m%d'),
                        "lat_lon_source": "website",
                    },
                    "lat": store.get("geoCoordinates", {}).get("latitude"),
                    "lon": store.get("geoCoordinates", {}).get("longitude"),
                    "name": store.get("shortTitle"),
                    "opening_hours": {"Opening_hours": self.parse_opening_hours(store.get("openingHours"))},
                    "phone": store.get("phoneNumber"),
                    "postcode": store.get("postalCode"),
                    "ref": store.get("shopId"),
                    "state": store.get("district"),
                    "website": f"{self.allowed_domains[0]}/us/en/{store.get('url')}",
                }

    def convert_to_24_hour_format(self, time_str):
        """Converts a 12-hour time format string (with AM/PM) to 24-hour time format."""
        time_str = time_str.strip().lower()
        if "am" in time_str:
            time_str = time_str.replace("am", "").strip()
            if time_str.startswith("12"):
                time_str = time_str.replace("12", "00", 1)
        elif "pm" in time_str:
            time_str = time_str.replace("pm", "").strip()
            if not time_str.startswith("12"):
                hours, minutes = time_str.split(":") if ":" in time_str else (time_str, "00")
                time_str = f"{int(hours) + 12}:{minutes}"

        return time_str

    def parse_opening_hours(self, opening_text):
        """Parse and convert opening hours from a text format to a structured format with 24-hour time."""
        hours_text = html.unescape(opening_text)

        days_map = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        abbr_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        hours_dict = {abbr: "Closed" for abbr in abbr_map}

        lines = re.findall(r"<li>.*?</li>", hours_text, re.DOTALL)
        if not lines:
            lines = [hours_text] 

        for line in lines:
            schedule_text = re.sub(r"</?li>", "", line).strip()

            if "Closed" in schedule_text:
                # Handle closed stores
                days_match = re.search(r"(Sunday|[A-Za-z]+(?:day)?)", schedule_text, re.IGNORECASE)
                if days_match:
                    day = days_match.group(0)
                    if day in days_map:
                        hours_dict[abbr_map[days_map.index(day)]] = "Closed"
                continue

            # Match days and opening hours
            matches = re.findall(
                r"([A-Za-z]+(?:day)?(?: to [A-Za-z]+(?:day)?)?)\s*-\s*((?:[\d:]+(?:\s*[ap]m)?(?:\s*to\s*[\d:]+(?:\s*[ap]m)?)?(?:\s*-\s*)?)+)",
                schedule_text,
                re.IGNORECASE,
            )

            for match in matches:
                days_part, hours_part = match
                hours_part = re.sub(r"\s+", " ", hours_part.strip())

                if " to " in days_part.lower():
                    start_day, end_day = [d.strip() for d in days_part.split(" to ")]
                    start_idx = days_map.index(start_day)
                    end_idx = days_map.index(end_day) + 1
                    for i in range(start_idx, end_idx):
                        hours_dict[abbr_map[i]] = " to ".join([self.convert_to_24_hour_format(t) for t in hours_part.split(" to ")])
                else:
                    if days_part in days_map:
                        hours_dict[abbr_map[days_map.index(days_part)]] = self.convert_to_24_hour_format(hours_part)

        return hours_dict
