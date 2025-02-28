import scrapy
import json
import re
import calendar
from urllib.parse import urlparse, parse_qs
from datetime import datetime

class StoreSpider(scrapy.Spider):
    name = "howell"
    allowed_domains = ["t.yapp.li"]
    start_urls = [
        "https://t.yapp.li/v1/cyan/margarethowell/shops/data?limit=1000&customorder=custom"
    ]

    def parse(self, response):
        # Assuming the data is a JSON response
        data = json.loads(response.text)
        
        website_url = response.url

        for store in data.get("contents", []):
            area = store.get("area", {}).get("label", "")
            
            details_lines = store.get("details", "").split("\n")
            
            postal_code = details_lines[0].replace("〒", "") if len(details_lines) > 0 else ""
            address_details = details_lines[1] if len(details_lines) > 1 else ""
            address_parts = address_details.split()
            
            # Format in japan: [Prefecture] [City] [Rest of address]
            prefecture = address_parts[0] if len(address_parts) > 0 else ""
            city = address_parts[1] if len(address_parts) > 1 else ""
            
            street = " ".join(address_parts[2:]) if len(address_parts) > 2 else ""
            country = "Japan"
            address_full = f"{street}, {city}, {prefecture}, {postal_code}, {country}"
            

            phone = details_lines[2].replace("TEL.", "").strip() if len(details_lines) > 2 else ""
            
            opening_hours = details_lines[3].replace("営業時間", "").strip() if len(details_lines) > 3 else ""

            map_url = store.get("map", "")
            lat, lon = self.extract_lat_lon_from_map(map_url)

            categories = [category.get("label") for category in store.get("categories", [])]

            yield {
                "addr_full": address_full,
                "brand": "margarethowell",  
                "city": city,
                "country": "Japan",  
                "extras": {
                    "brand": "margarethowell",  
                    "fascia": area,
                    "category": ", ".join(categories),  # Join all categories 
                    "edit_date": datetime.now().strftime('%Y%m%d'),
                    "lat_lon_source": "thirdparty"
                },
                "lat": lat,
                "long": lon,
                "name": store.get("name_en", ""),
                "opening_hours": {
                                    calendar.day_name[i][:3]: 
                                        opening_hours for i in range(7)
                                    },
                "phone": phone,
                "postcode": postal_code,
                "ref": store.get("_id", ""),
                "state": "",
                "website": website_url, 
            }

    def extract_lat_lon_from_map(self, map_url):
        # Extract latitude and longitude from Google Maps URL
        if "google.com" in map_url or "google.co.jp" in map_url:
            # Use regex to find latitude and longitude after '@' symbol
            match = re.search(r'/@(-?\d+\.\d+),(-?\d+\.\d+)', map_url)
            if match:
                lat = match.group(1)
                lon = match.group(2)
                return lat, lon
        return "", ""

