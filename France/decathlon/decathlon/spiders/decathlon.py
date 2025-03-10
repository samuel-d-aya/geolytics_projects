import scrapy
import json
import datetime

class DecathlonSpider(scrapy.Spider):
    name = "decathlon"
    start_urls = [
        'https://api.woosmap.com/stores/search?key=woos-c7283e70-7b4b-3c7d-bbfe-e65958b8769b&query=(user.publishOnEcommerce%3A1%20AND%20user.status%3A%22OPEN%22%20AND%20country%3A%22FR%22)&page=1'
    ]
    
    allowed_domains = ['api.woosmap.com']

    def parse(self, response):
        data = json.loads(response.text)
        day_mapping = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
        
        for store in data.get('features', []):
            properties = store.get('properties', {})
            weekly_opening = properties.get('weekly_opening', {})
            
            # Process opening hours
            formatted_opening_hours = {}
            for day_num_str, day_data in weekly_opening.items():
            
                if not day_num_str.isdigit():
                    continue
                    
                day_num = int(day_num_str)
                hours_list = day_data.get('hours', [])
                
                if hours_list and len(hours_list) > 0:
                    # Handle multiple time slots in a day by joining them
                    time_slots = []
                    for hours in hours_list:
                        if 'start' in hours and 'end' in hours:
                            time_slots.append(f"{hours['start']}-{hours['end']}")
                    
                    # Map 0 to 7 for Sunday if needed
                    day_key = 7 if day_num == 0 else day_num
                    formatted_opening_hours[day_mapping.get(day_num, "")] = ", ".join(time_slots)
                else:
                    day_key = 7 if day_num == 0 else day_num
                    formatted_opening_hours[day_mapping.get(day_num, "")] = ""
            
            # Get coordinates safely
            coordinates = store.get('geometry', {}).get('coordinates', [0, 0])
            longitude = coordinates[0] if len(coordinates) > 0 else None
            latitude = coordinates[1] if len(coordinates) > 1 else None
            
            yield {
                'address': properties.get('address', {}).get('lines', []),
                'brand': "Decathlon",
                'city': properties.get('address', {}).get('city'),
                'postcode': properties.get('address', {}).get('zipcode'),
                'country': properties.get('address', {}).get('country_code'),
                "extras": {
                    "brand": "Decathlon",
                    "fascia": "Decathlon",
                    "category": "Sports",
                    "edit_date": datetime.datetime.now().strftime('%Y%m%d'),
                    "lat_lon_source": "website",
                },
                'latitude': latitude,
                'longitude': longitude,
                'opening_hours': {"opening_hours":formatted_opening_hours},
                'name': properties.get('name'),
                'phone': properties.get('contact', {}).get('phone'),
                'ref': properties.get('store_id'),
                "state": "",
                'website': "https://www.decathlon.fr/store-locator"
            }
        
        # Handle pagination
        current_page = data.get('pagination', {}).get('page', 1)
        page_count = data.get('pagination', {}).get('pageCount', 1)
        
        if current_page < page_count:
            next_page = current_page + 1
            next_page_url = f'https://api.woosmap.com/stores/search?key=woos-c7283e70-7b4b-3c7d-bbfe-e65958b8769b&query=(user.publishOnEcommerce%3A1%20AND%20user.status%3A%22OPEN%22%20AND%20country%3A%22FR%22)&page={next_page}'
            yield scrapy.Request(url=next_page_url, callback=self.parse)