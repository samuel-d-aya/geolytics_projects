import scrapy
import json
import re
import datetime
from parsel import Selector


class MetroSpider(scrapy.Spider):
    name = "metro_stores"
    allowed_domains = ["metro.de"]

    def start_requests(self):
        url = (
            "https://www.metro.de/sxa/search/results"
            "?s=%7B0F3B38A3-7330-4544-B95B-81FC80A6BB6F%7D"
            "&v=%7BD5BC0757-6F6D-4BDB-BFBD-065D34D0B4A3%7D"
            "&p=102"
            "&o=StoreName,Ascending"
            "&g="
        )
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/135.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.metro.de/standorte?itm_pm=cookie_consent_accept_button",
            "X-Requested-With": "XMLHttpRequest",
            # Optional but safe to include:
            "Sec-CH-UA": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "Sec-CH-UA-Arch": '"x86"',
            "Sec-CH-UA-Bitness": '"64"',
            "Sec-CH-UA-Full-Version-List": '"Brave";v="135.0.0.0", "Not-A.Brand";v="8.0.0.0", "Chromium";v="135.0.0.0"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Model": '""',
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-CH-UA-Platform-Version": '"14.0.0"',
            # THIS is the critical one you still need to find:
            # "Cookie": "insert_your_cookie_string_here"
        }
        yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        data = json.loads(response.text)
        results = data.get("Results", [])

        for result in results:
            html = result.get("Html", "")
            sel = Selector(text=html)

            name = sel.css(".poi-store-name::text").get(default="").strip()
            addr = sel.css(".location-icon + a::text").get(default="").strip()
            phone = sel.css(".phone-icon + span a::text").get(default="").strip()
            store_id = sel.css("div.store-locator-details::attr(data-storeid)").get()
            latlon_link = sel.css(".location-icon + a::attr(href)").get()
            store_page = sel.css(".store-info-button::attr(href)").get()
            lat, lon = self.extract_lat_lon(latlon_link)

            # Extract and format opening hours
            days = sel.css(".day-title::text").getall()
            hours = sel.css(".day-hours::text").getall()
            opening_hours = self.parse_opening_hours(zip(days, hours))

            yield {
                "addr_full": addr,
                "brand": "Metro AG",
                "city": self.extract_city(addr),
                "country": "Germany",
                "extras": {
                    "brand": "Metro AG",
                    "fascia": "Metro AG",
                    "category": "Retail",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Third Party",
                },
                "lat": lat,
                "lon": lon,
                "name": name,
                "opening_hours": {"opening_hours":opening_hours},
                "phone": re.sub(r"[^\d+]", "", phone),
                "postcode": self.extract_postcode(addr),
                "ref": store_id,
                "state": None,  # Not clearly available from the page
                "website": response.urljoin(store_page),
            }
            
    def extract_city(self, addr):
        # Simple heuristic: city is usually after postcode
        match = re.search(r"\b\d{5}\s+([A-Za-zäöüÄÖÜß\s\-]+)", addr)
        return match.group(1).strip() if match else None
    
    def extract_postcode(self, addr):
        match = re.search(r"\b\d{5}\b", addr)
        return match.group(0) if match else None
    
    def extract_lat_lon(self, link):
        if not link:
            return None, None
        match = re.search(r"q=([\d.]+),([\d.]+)", link)
        if match:
            return float(match.group(1)), float(match.group(2))
        return None, None
    
    def parse_opening_hours(self, day_hour_pairs):
        day_map = {
            "Montag": "Mon",
            "Dienstag": "Tue",
            "Mittwoch": "Wed",
            "Donnerstag": "Thu",
            "Freitag": "Fri",
            "Samstag": "Sat",
            "Sonntag": "Sun",
        }

        opening_hours = {}
        for day, hours in day_hour_pairs:
            day_abbr = day_map.get(day)
            if not day_abbr or "geschlossen" in hours.lower():
                continue
            hours_clean = hours.replace(" ", "").replace("–", "-")  # Normalize dashes
            opening_hours[day_abbr] = hours_clean

        return opening_hours