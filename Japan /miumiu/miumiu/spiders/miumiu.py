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
        data = json.loads(response.text)
        website_url = response.url
        
        # Extract data
        location_data = data.get('response', {}).get('results', [])
        
        for location in location_data:
            
            location_info = location.get('data', {})
            
            address = location_info.get('address', {})
            country_code = address.get('countryCode') 
            
            # Only process if the country is JP (Japan)
            if country_code == 'JP':
                geocodedCoordinate = location_info.get('geoCoordinate', {})
                hours = location_info.get('hours', {})
                
                
                self.logger.info(f"Raw hours data for {location_info.get('name')}: {hours}")
                
                yield {
                    "addr_full": f"{address.get('line1', '')} {address.get('line2', '')}, {address.get('sublocality', '')}, {address.get('city', '')}, {address.get('region', '')} {address.get('postalCode', '')}",
                    "brand": "Miu Miu",  
                    "city": address.get('city',''),
                    "country": "Japan",  
                    "extras": {
                        "brand": "Miu Miu",  
                        "fascia": "Miu Miu",
                        "category": "Fashion ",  
                        "edit_date": datetime.now().strftime('%Y%m%d'),
                        "lat_lon_source": "Third Party"
                    },
                    "lat": geocodedCoordinate.get('latitude', ''),
                    "long": geocodedCoordinate.get('longitude', ''),
                    "name": location_info.get('name'),
                    "opening_hours": {"opening_hours":self.format_hours(hours)},
                    "phone": location_info.get('mainPhone'),
                    "postcode": address.get('postalCode',''),
                    "ref": location_info.get('id',''),
                    "state": "",
                    "website": website_url,
                }

    def format_hours(self, hours_data):
        opening_hours = {}
        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        for day in days_of_week:
            formatted_day = day.capitalize()[:3]
        
            day_schedule = hours_data.get(day, {})
        
            self.logger.info(f"Day {day} schedule: {day_schedule}")
            
            is_closed = (
                day_schedule.get('isClosed', False) or 
                not day_schedule or 
                (isinstance(day_schedule, dict) and not day_schedule.get('openIntervals'))
            )
            
            if not is_closed:
                open_times = []
                
                intervals = day_schedule.get('openIntervals', [])
                
            
                if isinstance(intervals, dict):
                    intervals = [intervals]
                elif not isinstance(intervals, list):
                    intervals = []
                
                for interval in intervals:
                    # Safely get start and end times
                    start = interval.get('start', '')
                    end = interval.get('end', '')
                    
                    if start and end:
                        open_times.append(f"{start}-{end}")
                
                if open_times:
                    opening_hours[formatted_day] = ' / '.join(open_times)
                else:
                    self.logger.warning(f"No open times found for {day}, but not marked as closed")
                    opening_hours[formatted_day] = "Closed"
            else:
                opening_hours[formatted_day] = "Closed"
        
        return opening_hours