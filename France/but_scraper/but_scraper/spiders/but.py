import scrapy
import json
import re
import datetime 
from scrapy_splash import SplashRequest
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

# Define your spider class
class ShopsSpider(scrapy.Spider):
    name = 'shops_spider'
    start_urls = ['https://www.but.fr/magasins/recherche-magasins']  # Replace with your target URL

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, args={'wait': 2})

    def parse(self, response):
        # Extract the script data
        script_data = response.css('body > script:nth-child(4)::text').get()

        if script_data:
            # Get the required fields
            try:
                # Find the start and end of the shop data
                start_index = script_data.find('appData.listShop = [')
                end_index = script_data.find('] ;', start_index)

                if start_index != -1 and end_index != -1:
                    # Extract the JSON part between the start and end index
                    json_data = script_data[start_index + len('appData.listShop = '): end_index + 1]
                    
                    # Parse the JSON data of the shops
                    shops = json.loads(json_data)
                    
                    # Iterate through the list of shops and extract details for each shop
                    for shop in shops:
                        # Prepare the final item with opening hours
                        item = {
                            'addr_full': shop.get('address', {}).get('streetAddress'),
                            'brand': 'But',
                            'city': shop.get('address', {}).get('city'),
                            'country': shop.get('address', {}).get('country'),
                            'extras': {
                                'brand': 'But',
                                'facia': 'But',
                                'category': 'Retail',
                                'edit_date': str(datetime.datetime.now().date()),
                                'lat_lon_source': 'website'
                            },
                            'lat': shop.get('geolocation', {}).get('latitude'),
                            'lon': shop.get('geolocation', {}).get('longitude'),
                            'name': shop.get('name'),
                            'phone': shop.get('phone', {}).get('phoneNumber'),
                            'postcode': shop.get('address', {}).get('zipCode'),
                            'ref': shop.get('id'),
                            "state": "",
                            'website': f'https://www.but.fr{shop.get("url")}'
                        }
                        yield item

            except Exception as e:
                self.log(f'Error extracting data: {e}')
        else:
            self.log('No script data found')

# Custom settings for your Scrapy project
custom_settings = {
    'BOT_NAME': 'mybot',
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'ROBOTSTXT_OBEY': False,  # Set to False if you want to ignore robots.txt
    'DOWNLOAD_DELAY': 1,  # Add delay between requests to prevent getting banned
    'FEED_FORMAT': 'csv',  # Output format (you can also use 'csv', 'xml', etc.)
    'FEED_URI': 'output.csv',# The file where the scraped data will be stored
    'CONCURRENT_REQUESTS': 1,  # Limit to 1 concurrent request for simplicity
    'LOG_LEVEL': 'INFO',  # Log level
}

# Create and configure the CrawlerProcess with custom settings
process = CrawlerProcess(settings=custom_settings)

# Start the spider
process.crawl(ShopsSpider)
process.start()
