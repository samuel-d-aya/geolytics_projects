import scrapy
import json
from scrapy.crawler import CrawlerProcess
from datetime import datetime

class BeamsShopSpider(scrapy.Spider):
    name = 'beams_shops'
    allowed_domains = ['beams.co.jp']
    
    # Start URL - the API endpoint for shop data
    start_urls = ['https://www.beams.co.jp/global/api/shop']
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
        'COOKIES_ENABLED': True,
        'FEED_EXPORT_ENCODING': 'utf-8-sig',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.beams.co.jp/global/shop/',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
        }
    }
    
    def parse(self, response):
        # Parse the initial API response
        shops_data = json.loads(response.body)
        
        for area in shops_data.get('shops', []):
            area_name = area.get('name_en', '')
            
            for sub_area in area.get('areas', []):
                sub_area_name = sub_area.get('name_en', '')
                
                for shop in sub_area.get('shops', []):
                    # Create the base shop item
                    shop_item = {
                        'area': area_name,
                        'sub_area': sub_area_name,
                        'shop_id': shop.get('id', ''),
                        'shop_name_en': shop.get('name_en', ''),
                        'url_param': shop.get('url_param', ''),
                        'link_url': shop.get('link_url', ''),
                        'address_en': shop.get('address_en', ''),
                        'description_en': shop.get('description_en', ''),
                        'tel': shop.get('tel_en', ''),
                        'image_url': shop.get('image_url', '')
                    }
                    
                    # If there's a link_url, follow it to get more details
                    if shop.get('link_url'):
                        detail_url = f"https://www.beams.co.jp{shop.get('link_url')}"
                        
                        # Pass the shop_item to the callback using meta
                        yield scrapy.Request(
                            url=detail_url,
                            callback=self.parse_shop_details,
                            meta={'shop_item': shop_item}
                        )
                    else:
                        # If no link_url, just yield the item as is
                        yield shop_item
    
    def parse_shop_details(self, response):
        # Get the shop_item from meta
        shop_item = response.meta['shop_item']
        
        # Extract detailed information from the detail page
        # Address (if not already present)
        if not shop_item['address_en']:
            address = response.css('dl:contains("Address") dd::text').get()
            if address:
                shop_item['address_en'] = address.strip()
        
        # Tel (if not already present)
        if not shop_item['tel']:
            tel = response.css('dl:contains("Tel") dd::text').get()
            if tel:
                shop_item['tel'] = tel.strip()
        
        # Add new fields
        shop_item['hours'] = response.css('dl:contains("Hours") dd::text').get('').strip()
        shop_item['open_days'] = response.css('dl:contains("Open") dd::text').get('').strip()
        
        # Check for services
        services = []
        for service in response.css('dl.service li'):
            service_name = service.css('img::attr(alt)').get('')
            if service_name:
                services.append(service_name)
        
        shop_item['services'] = ', '.join(services)
        
        # Extract Google Maps coordinates if available
        map_iframe = response.css('.map iframe::attr(src)').get()
        if map_iframe and 'll=' in map_iframe:
            coords_part = map_iframe.split('ll=')[1].split('&')[0]
            if coords_part and ',' in coords_part:
                lat, lng = coords_part.split(',')
                shop_item['latitude'] = lat
                shop_item['longitude'] = lng
        
        # Now yield the enriched item
        yield shop_item

# Run the spider if script is executed directly
if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(BeamsShopSpider)
    process.start()
