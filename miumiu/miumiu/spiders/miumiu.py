import scrapy
import json
import re
import calendar
from urllib.parse import urlparse, parse_qs
from datetime import datetime

class MiuMiuSpider(scrapy.Spider):
    name = "miumiu"
    start_urls = ['https://cdn.yextapis.com/v2/accounts/me/search/vertical/query?api_key=61119b3d853ae12bf41e7bd9501a718b&locale=en&v=20220511&limit=50&experienceKey=miumiu-experience&verticalKey=miumiu-locations&retrieveFacets=true&input=&offset=0&location=36.204824,138.252924&locationRadius=5000000']  # Replace with the actual URL containing the JSON data

    def parse(self, response):
        # Parse the JSON data from the response
        data = json.loads(response.text)
        website_url = response.url
        
        # Extract data
        location_data = data.get('response', {}).get('results', [])
        
        for location in location_data:
            
            location_info = location.get('data', {})
            
            address = location_info.get('address', {})
            country_code = address.get('countryCode')  # Get countryCode from address field
            
            # Only process if the country is JP (Japan)
            if country_code == 'JP':
                geocodedCoordinate = location_info.get('geoCoordinate', {})
                hours = location_info.get('hours', {})
                
                yield {
                    "addr_full": f"{address.get('line1', '')} {address.get('line2', '')}, {address.get('sublocality', '')}, {address.get('city', '')}, {address.get('region', '')} {address.get('postalCode', '')}",
                    "brand": "Miu Miu",  
                    "city": address.get('postalCode',''),
                    "country": country_code,  
                    "extras": {
                        "brand": "Miu Miu",  
                        "fascia": "Miu Miu",
                        "category": "Fashion ",  # Join all categories 
                        "edit_date": datetime.now().strftime('%Y%m%d'),
                        "lat_lon_source": "thirdparty"
                    },
                    "lat": geocodedCoordinate.get('latitude', ''),
                    "long": geocodedCoordinate.get('longitude', ''),
                    "name": location_info.get('name'),
                    "opening_hours": self.format_hours(hours),
                    "phone": location_info.get('mainPhone'),
                    "postcode": address.get('postalCode',''),
                    "ref": location_info.get('id',''),
                    "state": "",
                    "website": website_url,
                }

    def format_hours(self, hours_data):
        # Format the opening hours into the desired structure
        opening_hours = {}
        days_of_week = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        
        for day in days_of_week:
            # Check if the 'day' is present in the hours_data
            day_schedule = hours_data.get(day, {})
            
            # If the day is not closed, process the open intervals
            if day_schedule and not day_schedule.get('isClosed', True):
                open_times = [
                    f"{interval.get('start')}-{interval.get('end')}"
                    for interval in day_schedule.get('openIntervals', [])
                ]
                # Join multiple intervals with commas if applicable
                opening_hours[day.capitalize()] = ' / '.join(open_times) if open_times else "Closed"
            else:
                opening_hours[day.capitalize()] = "Closed"
        
        # Return the final formatted opening_hours
        return opening_hours
