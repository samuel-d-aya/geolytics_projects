import scrapy
import re
import datetime
import json

class AshSpider(scrapy.Spider):
    name = "ash"
    start_urls = ["https://www.the-ash.com/en/restaurants"]

    def parse(self, response):
        
        script_content = response.xpath('//*[@id="main"]/div/section/div/script[2]/text()').get()
        
        if script_content:
            locations_match = re.search(r'var locations\s*=\s*(\[.*?\]);', script_content, re.DOTALL)
            
            if locations_match:
                try:
                    locations_str = locations_match.group(1)
                    
                    locations_str = re.sub(r'\s+', ' ', locations_str)  # Remove extra spaces
                    locations_str = locations_str.replace(' [', '[').replace('] ', ']')  # Clean brackets
                    locations_str = locations_str.replace(' ,', ',').replace(', ', ',')  # Fix commas
                    
                    if locations_str.endswith(',]'):
                        locations_str = locations_str[:-2] + ']'
                    
                    locations = json.loads(locations_str)

                    for location in locations:
                        if len(location) >= 4:
                            city = location[0]
                            lat = location[1]
                            lon = location[2]
                            url = location[3]

                            if not url:
                                self.logger.warning(f"Missing URL for {city}")
                                continue 

                            yield response.follow(url, self.parse_location, meta={
                                'city': city, 
                                'lat': lat, 
                                'lon': lon
                            })

                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON Decode Error: {e}")
                    self.logger.error(f"Problematic locations string: {locations_str}")
            
            else:
                self.logger.error("Locations data could not be extracted from the script tag.")
                return 

    def parse_location(self, response):
        city = response.meta['city']
        lat = response.meta['lat']
        lon = response.meta['lon']

    
        address_selector = [
            '.location-text p::text'
        ]

        phone_selector = [
            '.location-text p::text'
        ]

        phone = None
        for selector in phone_selector:
            phone = response.css(selector).getall()[-1]
            if phone:
                break

        # Try multiple XPaths to extract address
        address = None
        for selector in address_selector:
            address = response.css(selector).getall()[-2]
            if address:
                break

        # Clean up extracted data
        phone = phone.strip() if phone else None
        address = address.strip() if address else None

        # Add brand and name
        brand = "ASH"
        name = f"{brand} {city}"

        opening_hours = self.extract_opening_hours(response)

        yield {
            'addr_full': address,
            'city': city,
            'country': "Germany",
            'brand': brand,
            'extras': {
                'brand': brand,
                'fascia': brand,
                'category': "Food & Beverage",
                'edit_date': str(datetime.datetime.now().date()),
                'lat_lon_source': "Third-party"
            },
            'lat': lat,
            'lon': lon,
            'ref': f"{lat}-{lon}",
            'opening_hours': opening_hours,
            'postcode': None,
            'name': name,
            'state': None,
            'phone': phone,
            'website': "https://www.the-ash.com/en/restaurants"
        }

    def extract_opening_hours(self, response):
        
        text = response.css('#opening-hours p::text').getall()


        text = [t.strip() for t in text if t.strip()]

        opening_hours = {}

        days_mapping = {
            "Monday - Thursday": ["Mon", "Tue", "Wed", "Thu"],
            "Friday": ["Fri"],
            "Saturday": ["Sat"],
            "Sunday & Holidays": ["Sun"]
        }

        for i in range(1, len(text), 2): 
            day_label = text[i]
            time = text[i + 1]

            for label, days_list in days_mapping.items():
                if label in day_label:
                    for day in days_list:
                        time_cleaned = time.replace(" Uhr", "")
                        opening_hours[day] = time_cleaned

        return {"opening_hours": opening_hours}
