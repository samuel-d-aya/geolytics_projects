import scrapy
import datetime
import json
import re

class AlexSpider(scrapy.Spider):
    name = "alex"
    allowed_domains = ["api.mabg.de"]
    start_urls = ["https://api.mabg.de/basedata/locations"]

    def parse(self, response):
        data = json.loads(response.text)
        for location in data:
            full_address = f"{location.get('street', '')} {location.get('streetNumber', '')}, {location.get('zip', '')} {location.get('city', '')}"
            city = location.get("city")
            zipcode = location.get("zip")
            phone = location.get("phone")
            location_id = location.get("id")
            opening_hours = location.get("openingTimes", {}).get("days", [])
            google_maps_link = location.get("googleMapsLink")

            # Extract latitude and longitude from the Google Maps link
            lat_lon_match = re.search(r"@([-.\d]+),([-.\d]+)", google_maps_link)
            if lat_lon_match:
                lat = float(lat_lon_match.group(1))
                lon = float(lat_lon_match.group(2))
            else:
                lat = None
                lon = None
                
            # Convert opening hours to the desired format
            formatted_opening_hours = {}
            day_mapping = {
                "MON": "Mon",
                "TUE": "Tue",
                "WED": "Wed",
                "THU": "Thu",
                "FRI": "Fri",
                "SAT": "Sat",
                "SUN": "Sun",
            }

            for day in opening_hours:
                if day.get("isOpen"):
                    day_name = day_mapping.get(day["name"], day["name"])
                    open_time = day["from"]
                    close_time = day["to"]
                    
                    formatted_opening_hours[day_name] = f"{open_time}-{close_time}"

            yield {
                "addr_full": full_address,
                "city": city,
                "country": "Germany",
                "brand": "ALEX",
                "extras": {
                    "brand": "ALEX",
                    "fascia": "ALEX",
                    "category": "Food & Beverage",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party",
                },
                "latitude": lat,
                "longitude": lon,
                "opening_hours": {"opening_hours": formatted_opening_hours},
                "phone": phone,
                "ref": location_id,
                "postcode": zipcode,
                "name": location.get("name"),
                "state": None,
                "website": f"{"https://www.dein-alex.de/"}{city}",
            }
            
    
