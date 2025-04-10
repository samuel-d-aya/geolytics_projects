import scrapy
from urllib.parse import urljoin, urlparse, parse_qs
import re
import json
import requests
import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

class PizzaSpider(scrapy.Spider):
    name = 'worldofpizza'
    start_urls = ['https://www.world-of-pizza.de/']
    
    
    day_mapping = {
        'Mo': 'Mon',
        'Di': 'Tue',
        'Mi': 'Wed',
        'Do': 'Thu',
        'Fr': 'Fri',
        'Sa': 'Sat',
        'So': 'Sun'
    }
    
    
    def __init__(self, *args, **kwargs):
        super(PizzaSpider, self).__init__(*args, **kwargs)
        self.geolocator = Nominatim(user_agent="world-of-pizza-spider")
        
    def parse(self, response):
        shop_links = response.css('#menu-item-619 > ul a::attr(href)').getall()

        for link in shop_links:
            absolute_url = urljoin(response.url, link)
            
            yield response.follow(absolute_url, callback=self.parse_shop_details)
            
    def parse_shop_details(self, response):
        try:
            shop_name = response.css('h1::text').get()
            shop_name = shop_name.strip() if shop_name else "Not found"
            
            street_address = "Not found"
            postal_code = "Not found"
            city = "Not found"
            
            first_address_parts = response.css('.el-place .el-content p:nth-child(1)::text').getall()
            first_address_parts = [part.strip() for part in first_address_parts if part.strip()]
            
            second_address_parts = response.css('.el-place .el-content p:nth-child(2)::text').getall()
            second_address_parts = [part.strip() for part in second_address_parts if part.strip()]
            
            valid_address_found = False
            
            if first_address_parts:
                full_address_match = re.search(r'(.*),\s*(\d{5})\s+(.*)', first_address_parts[0])
                if full_address_match:
                    street_address = full_address_match.group(1).strip()
                    postal_code = full_address_match.group(2).strip()
                    city = full_address_match.group(3).strip()
                    valid_address_found = True
                elif len(first_address_parts) > 1:
                    
                    street_address = first_address_parts[0].rstrip(',')
                    
                    postal_city = first_address_parts[1].strip()
                    postal_match = re.search(r'\b(\d{5})\b\s*(.*)', postal_city)
                    
                    if postal_match:
                        postal_code = postal_match.group(1)
                        city = postal_match.group(2).strip()
                        valid_address_found = True
            
            if not valid_address_found and second_address_parts:
                second_address = second_address_parts[0] if second_address_parts else ""
                if second_address:
                    alt_address_match = re.search(r'(.*),\s*(\d{5})\s+(.*)', second_address)
                    
                    if alt_address_match:
                        street_address = alt_address_match.group(1).strip()
                        postal_code = alt_address_match.group(2).strip()
                        city = alt_address_match.group(3).strip()
                        valid_address_found = True
                    elif ',' in second_address:
                        street_address = second_address.split(',')[0].strip()
                        remainder = second_address.split(',')[1].strip()
                        postal_match = re.search(r'\b(\d{5})\b\s*(.*)', remainder)
                        if postal_match:
                            postal_code = postal_match.group(1)
                            city = postal_match.group(2).strip()
                            valid_address_found = True
            
            if not valid_address_found and first_address_parts and second_address_parts:
                potential_street = first_address_parts[0].rstrip(',')
                potential_postal_city = second_address_parts[0].strip()
                
                postal_match = re.search(r'\b(\d{5})\b\s*(.*)', potential_postal_city)
                if postal_match:
                    street_address = potential_street
                    postal_code = postal_match.group(1)
                    city = postal_match.group(2).strip()
                    valid_address_found = True
                
            
                if not valid_address_found:
                    combined_address = ' '.join(first_address_parts + second_address_parts)
                    combined_match = re.search(r'(.*),\s*(\d{5})\s+(.*)', combined_address)
                    if combined_match:
                        street_address = combined_match.group(1).strip()
                        postal_code = combined_match.group(2).strip()
                        city = combined_match.group(3).strip()
                        valid_address_found = True
            
            
            if not valid_address_found:
                for para_num in range(3, 5):
                    para_text = response.css(f'.el-place .el-content p:nth-child({para_num})::text').get()
                    if para_text and re.search(r'\d{5}', para_text): 
                        para_text = para_text.strip()
                        address_match = re.search(r'(.*),\s*(\d{5})\s+(.*)', para_text)
                        
                        if address_match:
                            street_address = address_match.group(1).strip()
                            postal_code = address_match.group(2).strip()
                            city = address_match.group(3).strip()
                            valid_address_found = True
                            break
                        
                        postal_match = re.search(r'\b(\d{5})\b\s*(.*)', para_text)
                        if postal_match and street_address != "Not found":
                            postal_code = postal_match.group(1)
                            city = postal_match.group(2).strip() if postal_match.group(2) else "Not found"
                            valid_address_found = True
                            break

            map_link = response.css('.el-place .el-content ul li a[href*="maps"]::attr(href)').get()
            if not map_link:
                map_link = response.css('.el-place .el-content li:nth-child(2) > a::attr(href)').get()
            map_link = map_link.strip() if map_link else "Not found"
            
            latitude, longitude = self.extract_coordinates_from_map_link(map_link)

            if latitude == "Not found" or longitude == "Not found":
                if valid_address_found:
                    full_address = f"{street_address}, {postal_code} {city}, Germany"
                    self.logger.info(f"Geocoding address: {full_address}")
                    latitude, longitude = self.geocode_address(full_address)

            shop_phone = response.css('.el-place .el-content p:nth-child(2) a::text').get()
            if not shop_phone:
                shop_phone = response.css('.el-place .el-content p:nth-child(3) a::text').get()
            shop_phone = shop_phone.strip() if shop_phone else "Not found"

            raw_opening_hours = response.css('.el-place .el-content p:nth-child(3)::text').get()
            if not raw_opening_hours:
                raw_opening_hours = response.css('.el-place .el-content p:nth-child(4)::text').get()
            
        
            hours_dict = self.parse_opening_hours(raw_opening_hours)

            
            ref = f"{latitude}-{longitude}" if latitude != "Not found" and longitude != "Not found" else f"{postal_code}-{city}-{street_address}"

           
            yield {
                'addr_full': street_address,
                'city': city,
                'map_link': map_link,
                'country': 'Germany',
                'brand': 'World of Pizza',
                'extras': {
                    'brand': 'World of Pizza',
                    'fascia': 'World of Pizza',
                    'category': 'Food & Beverage',
                    'edit_date': str(datetime.datetime.now().date()),
                    'lat_lon_source': 'Third-party'
                },
                'lat': latitude,
                'lon': longitude,
                'opening_hours': hours_dict,
                'phone': shop_phone,
                'ref': ref,
                'postcode': postal_code,
                'shop_name': shop_name,
                'state': None,
                'website': response.url
            }
        except Exception as e:
            self.logger.error(f"Error processing {response.url}: {e}")
            yield {
                'shop_link': response.url,
                'error': str(e)
            }
    
    def geocode_address(self, address):
        
        try:
            
            for attempt in range(3):
                try:
                    location = self.geolocator.geocode(address, timeout=10)
                    if location:
                        return str(location.latitude), str(location.longitude)
                    break
                except GeocoderTimedOut:
                    self.logger.warning(f"Geocoder timed out on attempt {attempt + 1}")
                    # Wait a bit longer with each retry
                    import time
                    time.sleep(2 * (attempt + 1))
        except Exception as e:
            self.logger.error(f"Error geocoding address '{address}': {e}")
        
        return "Not found", "Not found"
    
    def extract_coordinates_from_map_link(self, map_link):
       
       
        latitude = "Not found"
        longitude = "Not found"
        
        if map_link == "Not found":
            return latitude, longitude
            
        try:
            
            full_map_url = map_link
            
            
            shortened_domains = ['goo.gl', 'bit.ly', 'tinyurl.com', 't.co', 'maps.app.goo.gl']
            parsed_url = urlparse(map_link)
            
            if any(domain in parsed_url.netloc for domain in shortened_domains) or len(parsed_url.path) < 20:
                try:
                    self.logger.info(f"Following shortened URL: {map_link}")
                    session = requests.Session()
                
                    response = session.get(map_link, allow_redirects=True, timeout=10)
                    full_map_url = response.url
                    self.logger.info(f"Resolved to: {full_map_url}")
                except Exception as e:
                    self.logger.error(f"Error following shortened URL '{map_link}': {e}")
                    
                    full_map_url = map_link
            
           
            coord_pattern = r'[?&@](?:place/[^/]+/)?(-?\d+\.\d+),(-?\d+\.\d+)'
            coord_match = re.search(coord_pattern, full_map_url)
            
            if coord_match:
                latitude = coord_match.group(1)
                longitude = coord_match.group(2)
                return latitude, longitude
            
        
            parsed_url = urlparse(full_map_url)
            query_params = parse_qs(parsed_url.query)
            
            if 'll' in query_params and query_params['ll'][0]:
                ll_parts = query_params['ll'][0].split(',')
                if len(ll_parts) >= 2:
                    latitude = ll_parts[0].strip()
                    longitude = ll_parts[1].strip()
                    return latitude, longitude
            
            
            path_pattern = r'/data=([^/]+)/|/data=([^?]+)'
            path_match = re.search(path_pattern, full_map_url)
            
            if path_match:
                data_str = path_match.group(1) or path_match.group(2)
                coord_pattern = r'(-?\d+\.\d+),(-?\d+\.\d+)'
                coord_match = re.search(coord_pattern, data_str)
                
                if coord_match:
                    latitude = coord_match.group(1)
                    longitude = coord_match.group(2)
                    return latitude, longitude
            
            
            general_pattern = r'[-+=](-?\d+\.\d+),(-?\d+\.\d+)'
            general_match = re.search(general_pattern, full_map_url)
            
            if general_match:
                latitude = general_match.group(1)
                longitude = general_match.group(2)
                return latitude, longitude
            
            if not (latitude != "Not found" and longitude != "Not found"):
                try:
                    session = requests.Session()
                    response = session.get(full_map_url, timeout=10)
                    content = response.text
                    
                    content_pattern = r'center=(-?\d+\.\d+),(-?\d+\.\d+)|latlng[\'\":\s]+(-?\d+\.\d+),(-?\d+\.\d+)'
                    content_match = re.search(content_pattern, content)
                    
                    if content_match:
                        lat_group = content_match.group(1) or content_match.group(3)
                        lng_group = content_match.group(2) or content_match.group(4)
                        
                        if lat_group and lng_group:
                            latitude = lat_group
                            longitude = lng_group
                            return latitude, longitude
                except Exception as e:
                    self.logger.error(f"Error retrieving content from '{full_map_url}': {e}")
        
        except Exception as e:
            self.logger.error(f"Error extracting coordinates from map link '{map_link}': {e}")
            
        return latitude, longitude
    
    def parse_opening_hours(self, hours_text):
        
        if not hours_text or hours_text == "Not found":
            return {
                'Mon': 'Closed', 'Tue': 'Closed', 'Wed': 'Closed', 
                'Thu': 'Closed', 'Fri': 'Closed', 'Sat': 'Closed', 'Sun': 'Closed'
            }
        
        hours_dict = {
            'Mon': 'Closed', 'Tue': 'Closed', 'Wed': 'Closed', 
            'Thu': 'Closed', 'Fri': 'Closed', 'Sat': 'Closed', 'Sun': 'Closed'
        }
        
        try:
            hours_text = hours_text.strip()
            
            range_pattern = r'([A-Za-z]{2})\s*[–\-]\s*([A-Za-z]{2})\s*(\d{1,2}:\d{2})\s*[–\-]\s*(\d{1,2}:\d{2})'
            single_pattern = r'([A-Za-z]{2})\s*(\d{1,2}:\d{2})\s*[–\-]\s*(\d{1,2}:\d{2})'
            
            range_match = re.search(range_pattern, hours_text)
            if range_match:
                start_day_abbr = range_match.group(1)
                end_day_abbr = range_match.group(2)
                open_time = range_match.group(3)
                close_time = range_match.group(4)
                
               
                start_day = self.day_mapping.get(start_day_abbr, start_day_abbr)
                end_day = self.day_mapping.get(end_day_abbr, end_day_abbr)
                
                
                days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                start_idx = days_order.index(start_day)
                end_idx = days_order.index(end_day)
                
                
                if start_idx > end_idx:
                    end_idx += 7
                
                for i in range(start_idx, end_idx + 1):
                    day_idx = i % 7
                    hours_dict[days_order[day_idx]] = f"{open_time}-{close_time}"
                
                return hours_dict
            
            
            for line in hours_text.split('\n'):
                single_match = re.search(single_pattern, line)
                if single_match:
                    day_abbr = single_match.group(1)
                    open_time = single_match.group(2)
                    close_time = single_match.group(3)
                    day = self.day_mapping.get(day_abbr, day_abbr)
                    if day in hours_dict:
                        hours_dict[day] = f"{open_time}-{close_time}"
            
            
            if all(value == 'Closed' for value in hours_dict.values()) and hours_text:
                
                times_match = re.search(r'(\d{1,2}:\d{2})\s*[–\-]\s*(\d{1,2}:\d{2})', hours_text)
                if times_match:
                    open_time = times_match.group(1)
                    close_time = times_match.group(2)
        
                    for day in hours_dict:
                        hours_dict[day] = f"{open_time}-{close_time}"
        
        except Exception as e:
            self.logger.error(f"Error parsing hours '{hours_text}': {e}")
        
        return hours_dict