import scrapy
import json
from scrapy.crawler import CrawlerProcess
from datetime import datetime

class BeamsShopSpider(scrapy.Spider):
    name = 'beams_shops'
    allowed_domains = ['beams.co.jp']
    
    start_urls = ['https://www.beams.co.jp/global/api/shop']
    
    base_url = 'https://www.beams.co.jp'
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 1,
        'DOWNLOAD_TIMEOUT': 360,
        'COOKIES_ENABLED': True,
        'FEED_FORMAT': 'csv',
        'FEED_URI': 'beams_shops.csv',
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
        try:
            response_data = json.loads(response.text)
            
            with open('beams_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            for area_name, areas in response_data['data'].items():
                for sub_area_name, shops in areas.items():
                    for shop in shops:
                        shop_item = {
                            'city': area_name,
                            'address_en': shop.get('address_en', ''),
                            'country': "Japan",
                            'ref': shop.get('id', ''),
                            'name': shop.get('name_en', ''),
                             "extras": {
                                    "brand": "Beams",
                                    "fascia": "Beams",
                                    "category": "Retail",
                                    "edit_date": datetime.now().strftime('%Y%m%d'),
                                    "lat_lon_source": "thirdparty",
                                },
                            'phone': shop.get('tel_en', ''),
                            'website': self.base_url + shop.get('link_url', ''),
                        }

                        # Follow the link to get more details
                        link_url = shop.get('link_url', '')
                        if link_url:
                            detail_url = f"https://www.beams.co.jp{link_url}"
                            yield scrapy.Request(
                                url=detail_url,
                                callback=self.parse_shop_details,
                                meta={'shop_item': shop_item} 
                            )
                        else:
                            
                            yield shop_item

        except json.JSONDecodeError as e:
            self.logger.error(f'Failed to parse JSON response: {e}')
        except Exception as e:
            self.logger.error(f'Error processing response: {e}')

    def parse_shop_details(self, response):
        
        self.logger.info(f"Parsing details for {response.url}")
        shop_item = response.meta['shop_item']
        
    
        
        # Opening hours
        hours = response.css('dl:contains("Hours") dd::text').get()
        if hours:
            shop_item['hours'] = hours.strip()
        
        
        
        # Google Maps coordinates (latitude and longitude) from iframe
        map_iframe = response.css('.map iframe::attr(src)').get()
        if map_iframe and 'll=' in map_iframe:
            coords_part = map_iframe.split('ll=')[1].split('&')[0]
            if coords_part and ',' in coords_part:
                lat, lng = coords_part.split(',')
                shop_item['latitude'] = lat
                shop_item['longitude'] = lng
        
        
        yield shop_item


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(BeamsShopSpider)
    process.start()
