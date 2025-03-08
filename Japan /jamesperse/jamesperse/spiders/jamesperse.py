import scrapy
import json
import re
import calendar
from urllib.parse import urlparse, parse_qs
from datetime import datetime

def convert_time(time_str):
    # Convert 12-hour format to 24-hour format
    from datetime import datetime
    try:
        return datetime.strptime(time_str.strip(), "%I:%M%p").strftime("%H:%M")
    except ValueError:
        return "CLOSED"

class StoreSpider(scrapy.Spider):
    name = "james"
    allowed_domains = ["https://www.jamesperse.com"]
    start_urls = [
        "https://stockist.co/api/v1/u8774/locations/all"
    ]

    def parse(self, response):
       
        data = json.loads(response.text)
        
        website_url = response.url
        
        contents = data

        # Filter 
        store_data = [store for store in contents if store.get('country','').lower() == 'japan']
        
        day_mapping = {
                        "Monday": "Mon",
                        "Tuesday": "Tue",
                        "Wednesday": "Wed",
                        "Thursday": "Thu",
                        "Friday": "Fri",
                        "Saturday": "Sat",
                        "Sunday": "Sun"
                    }
        
        for store in store_data:
            # Skip stores without description
            if not store.get('description'):
                continue

            # Handle opening hours with error checking
            try:
                opening_hours = {
                    day_mapping[day.split()[0]]: f"{convert_time(day.split()[1])}-{convert_time(day.split()[3])}" 
                    for day in store.get('description', '').split("\n") 
                    if day.split()[0] in day_mapping
                }
            except Exception:
                opening_hours = {}

            yield {
                "addr_full": store.get('address_line_1'),
                "brand": "James Perse",  
                "city":store.get('city'),
                "country": "Japan",  
                "extras": {
                    "brand": "James Perse",  
                    "fascia": "James Perse",
                    "category": "Fashion", 
                    "edit_date": datetime.now().strftime('%Y%m%d'),
                    "lat_lon_source": "Third Party"
                },
                "lat": store.get('latitude'),
                "long": store.get('longitude'),
                "name": store.get('name'),
                "opening_hours": opening_hours,
                "phone": store.get('phone'),
                "postcode": store.get('postal_code'),
                "ref": store.get("id", ""),
                "state": store.get('state',""),
                "website": "https://www.jamesperse.com/pages/store-locator", 
            }