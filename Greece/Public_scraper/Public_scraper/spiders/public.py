import scrapy
import json
import datetime
import re

class PublicStoresSpider(scrapy.Spider):
    name = "public"
    allowed_domains = ["public.gr"]

    def start_requests(self):
        url = "https://www.public.gr/public/v1/mm/stores?acs=all&isCheckout=false&locale=el"
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "cookie": "language=el-GR; DYN_USER_ID=8574311404; DYN_USER_CONFIRM=cdfc0abcce948351f9232a3a4a1f8d4b; JSESSIONID=z-u8jJ6BePoppLYbefwvpHAHb_6OCw3k6dJcsEqWx6_-x1Vo2c04!702442736; J2ROUTE=.route14; 8574311404_oc=0; CITRUS_AD_ID=ea12330e9054a5967a89c7bfa9a1d15898d2f2834572c0c31590f494114a54b8",
            "referer": "https://www.public.gr/store-locator/list",
            "sec-ch-ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        }

        yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse_opening_hours(self, html_string):
        if not html_string:
            self.logger.info("Empty HTML string received")
            return {}

        self.logger.info(f"RAW HTML: {html_string}")
        
        # Deep debugging of the HTML content
        html_content = html_string.replace("\\n", "\n").replace("\\r", "")
        self.logger.info(f"HTML after newline processing: {html_content}")
        
        # First, convert <br> tags to newlines to preserve line breaks (case insensitive)
        text = re.sub(r"<br\s*/?>", "\n", html_content, flags=re.IGNORECASE)
        self.logger.info(f"After BR replacement: {text}")
        
        # Remove HTML tags and decode entities
        # Use a more robust approach to handle various HTML structures
        text = re.sub(r"<!DOCTYPE.*?>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<html.*?>|</html>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<head.*?>.*?</head>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<body.*?>|</body>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<p.*?>|</p>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]*>", "", text)
        text = text.replace("&nbsp;", " ").strip()
        
        self.logger.info(f"After HTML tag removal: '{text}'")
        
        # Split the text by lines to handle the format better
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        self.logger.info(f"Extracted lines: {lines}")
        
        # Process each line separately
        day_segments = lines
        self.logger.info(f"Day segments to process: {day_segments}")
        
        greek_to_eng = {
            "Δευτέρα": "Mon", "Δευ": "Mon",
            "Τρίτη": "Tue", "Τριτ": "Tue",
            "Τετάρτη": "Wed", "Τετ": "Wed",
            "Πέμπτη": "Thu", "Πέμπ": "Thu",
            "Παρασκευή": "Fri", "Παρασ": "Fri",
            "Σάββατο": "Sat", "Σάβ": "Sat",
            "Κυριακή": "Sun", "Κυρ": "Sun",
        }

        ordered_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        opening_hours = {}

        # Prepare regexes outside the loop
        day_range_pattern = r"([Α-Ωα-ω]+)\s*-\s*([Α-Ωα-ω]+)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})"
        single_day_pattern = r"([Α-Ωα-ω]+)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})"
        closed_pattern = r"([Α-Ωα-ω]+)\s+[Κκ]λειστ[άό]"

        # Sort Greek days by length for most specific match first
        greek_days = sorted(greek_to_eng.keys(), key=len, reverse=True)

        for segment in day_segments:
            segment = segment.strip()
            self.logger.info(f"Processing segment: '{segment}'")
            
            # Try to match with different patterns
            # 1. Day range with hours
            day_range_match = re.search(day_range_pattern, segment)
            if day_range_match:
                day_from, day_to, time_from, time_to = day_range_match.groups()
                self.logger.info(f"Day range match found: {day_from} to {day_to}, {time_from}-{time_to}")
                
                # Find best match for day names
                d1 = None
                d2 = None
                
                for greek_day in greek_days:
                    if greek_day in day_from and not d1:
                        d1 = greek_to_eng[greek_day]
                        self.logger.info(f"Matched start day: {greek_day} -> {d1}")
                    if greek_day in day_to and not d2:
                        d2 = greek_to_eng[greek_day]
                        self.logger.info(f"Matched end day: {greek_day} -> {d2}")
                
                if d1 and d2:
                    i1 = ordered_days.index(d1)
                    i2 = ordered_days.index(d2)
                    for d in ordered_days[i1:i2 + 1]:
                        opening_hours[d] = f"{time_from}-{time_to}"
                        self.logger.info(f"Added range day: {d}: {time_from}-{time_to}")
                else:
                    self.logger.info(f"Failed to match day names in range: {day_from}-{day_to}")
                continue
            
            # 2. Single day with hours
            single_day_match = re.search(single_day_pattern, segment)
            if single_day_match:
                day, time_from, time_to = single_day_match.groups()
                self.logger.info(f"Single day match found: {day}, {time_from}-{time_to}")
                
                d = None
                for greek_day in greek_days:
                    if greek_day in day:
                        d = greek_to_eng[greek_day]
                        self.logger.info(f"Matched single day: {greek_day} -> {d}")
                        break
                
                if d:
                    opening_hours[d] = f"{time_from}-{time_to}"
                    self.logger.info(f"Added single day: {d}: {time_from}-{time_to}")
                else:
                    self.logger.info(f"Failed to match day name: {day}")
                continue
            
            # 3. Closed days
            closed_match = re.search(closed_pattern, segment, re.IGNORECASE)
            if closed_match:
                day = closed_match.group(1)
                self.logger.info(f"Closed day match found: {day}")
                
                d = None
                for greek_day in greek_days:
                    if greek_day in day:
                        d = greek_to_eng[greek_day]
                        self.logger.info(f"Matched closed day: {greek_day} -> {d}")
                        break
                
                if d:
                    opening_hours[d] = "closed"
                    self.logger.info(f"Added closed day: {d}")
                else:
                    self.logger.info(f"Failed to match closed day name: {day}")
                continue
            
            # No pattern matched
            self.logger.info(f"No pattern matched for segment: '{segment}'")
        
        self.logger.info(f"FINAL opening_hours: {opening_hours}")
        return opening_hours


    def parse(self, response):
        data = json.loads(response.text)
        stores = data.get("storesDto", {}).get("stores", [])
        for store in stores:
            yield {
                "addr_full": store.get("address1"),
                "brand": "Public",
                "city": store.get("city"),
                "country": store.get("country"),
                "extras": {
                    "brand": "Public",
                    "fascia": "Public",
                    "category": "Retail",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Third Party",
                },
                "lon": store.get("longitude"),
                "lat": store.get("latitude"),
                "name": store.get("name"),
                "opening_hours": self.parse_opening_hours(store.get("hours")),  # Parsing opening hours
                "phone": store.get("phoneNumber"),
                "postalCode": store.get("postalCode"),
                "ref": store.get("externalLocationId"),
                "state": store.get("area"),
                "website": store.get("url"),
            }
