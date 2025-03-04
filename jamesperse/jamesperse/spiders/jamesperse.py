import scrapy
import json
import re
import calendar
from urllib.parse import urlparse, parse_qs
from datetime import datetime

class StoreSpider(scrapy.Spider):
    name = "howell"
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
            yield {
                "addr_full": store.get('address_line_1'),
                "brand": "James Perse",  
                "city":store.get('city'),
                "country": store.get('country'),  
                "extras": {
                    "brand": "James Perse",  
                    "fascia": "James Perse",
                    "category": "Fashion", 
                    "edit_date": datetime.now().strftime('%Y%m%d'),
                    "lat_lon_source": "thirdparty"
                },
                "lat": store.get('latitude'),
                "long": store.get('longitude'),
                "name": store.get('name'),
                "opening_hours": {"Opening Hours": {
                                   " ".join(
                                            line.replace(day, day_mapping[day]) 
                                            for day in day_mapping 
                                            for line in store.get('description').split("\n") 
                                            if line.startswith(day)
)
                                    }},
                "phone": store.get('phone'),
                "postcode": store.get('postal_code'),
                "ref": store.get("_id", ""),
                "state": store.get('state',""),
                "website": website_url, 
            }
        