import scrapy
import json
import urllib.parse
import datetime

class StoreLocatorSpider(scrapy.Spider):
    name = 'doitcenter'
    allowed_domains = ['doitcenter.com.pa']
    start_urls = [
        'https://www.doitcenter.com.pa/api/graphql?query=query%20storeLocatorStores(%24pageSize%3AInt%24currentPage%3AInt%24product_sku%3AString%24same_day_pickup%3ABoolean%24filter%3AAmStoreLocationsFilterInput)%7BsearchAmStoreLocations(pageSize%3A%24pageSize%20currentPage%3A%24currentPage%20product_sku%3A%24product_sku%20same_day_pickup%3A%24same_day_pickup%20filter%3A%24filter)%7Bitems%7Bid%20name%20country%20city%20zip%20state%20address%20lat%20lng%20distance%20images%7Bid%20image_name%20is_base%7Ddescription%20phone%20email%20website%20schedule_string%20marker_img%20url_key%20average_rating%20meta_keywords%20meta_description%20meta_robots%20short_description%20canonical_url%20description%20main_image_name%20attributes%7Battribute_code%20frontend_label%20value%7Dfulfilments%7Bcode%20label%20date%20qty%20available%7D%7Dtotal_count%7D%7D&operationName=storeLocatorStores&variables=%7B%22pageSize%22%3A1000%2C%22currentPage%22%3A1%2C%22locale%22%3A%22es%22%7D']

    def start_requests(self):
        # Loop through the start_urls (in case of pagination or additional URLs)
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # Parse the JSON response
        data = response.json()
        stores = data['data']['searchAmStoreLocations']['items']

        # Extract data and yield it
        for store in stores:
            
            opening_hours = self.process_schedule(store['schedule_string'])
            
            yield {
                'addr_full': store['address'],
                'city': store['city'],
                'country': store['country'],
                'brand': 'Doitcenter',
                'extra': {
                    'brand': 'Doitcenter',
                    'fascia': 'Doitcenter',
                    'category': 'Retail',
                    'edit_date': datetime.datetime.now().strftime("%Y%m%d"),
                    'lat_lon_source': 'Third Party',
                },
                'lat': store['lat'],
                'lng': store['lng'],
                'opening_hours': opening_hours['opening_hours'],
                'phone': store['phone'],
                'ref': store['id'],
                'postcode': store['zip'],
                'name': store['name'],
                'state': store['state'],
                'website': store['website']
                
            }
    def process_schedule(self, schedule_string):
        # Parse the schedule_string JSON
        schedule = json.loads(schedule_string)

        # Prepare a dictionary to store opening hours
        opening_hours = {}

        # Days of the week mapping
        days_mapping = {
            "monday": "Mon", "tuesday": "Tue", "wednesday": "Wed", "thursday": "Thu",
            "friday": "Fri", "saturday": "Sat", "sunday": "Sun"
        }

        # Loop through each day and format the hours
        for day, day_abbr in days_mapping.items():
            day_schedule = schedule.get(day, {})
            if day_schedule.get(f"{day}_status") == "1":  # Check if open
                from_hour = day_schedule.get("from", {})
                to_hour = day_schedule.get("to", {})
                
                # Extract the hours and minutes, and format them
                from_time = f"{int(from_hour['hours']):02}:{int(from_hour['minutes']):02}"
                to_time = f"{int(to_hour['hours']):02}:{int(to_hour['minutes']):02}"

                opening_hours[day_abbr] = f"{from_time}-{to_time}"

        # Return the formatted opening_hours dictionary
        return {"opening_hours": opening_hours}
