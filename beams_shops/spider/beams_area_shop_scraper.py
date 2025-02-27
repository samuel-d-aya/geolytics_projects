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
        'DOWNLOAD_DELAY': 1,
        'COOKIES_ENABLED': True,
        'FEED_FORMAT': 'csv',
        'FEED_URI': f'beams_shops_{datetime.now().strftime("%Y%m%d")}.csv',
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
            # Parse the JSON response
            response_data = json.loads(response.text)
            
            # Save the raw response for reference (optional)
            with open('beams_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            shop_count = 0
            
            if 'status' in response_data and response_data['status'] == 1 and 'data' in response_data:
                # Extract the 'data' dictionary which contains the area and sub-area information
                data_container = response_data['data']
                
                # Iterate through the areas
                for area_name, sub_area_data in data_container.items():
                    self.logger.info(f"Processing area: {area_name}")
                    
                    # Iterate through the sub-areas
                    for sub_area_name, shops in sub_area_data.items():
                        self.logger.info(f"  Processing sub-area: {sub_area_name} with {len(shops)} shops")
                        
                        # Process each shop in the sub-area
                        for shop in shops:
                            shop_count += 1
                            
                            # shop items with area and sub area information
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
                            
                            # Add additional fields if any
                            for key, value in shop.items():
                                if key not in shop_item and isinstance(value, (str, int, float, bool)):
                                    shop_item[key] = value
                            
                            yield shop_item
            
            # If no shops found in the structured data, try recursive search
            if shop_count == 0:
                self.logger.warning("No shops found in the expected structure. Trying alternative approach.")
                # Recursive search logic here (not implemented for brevity)

        except json.JSONDecodeError as e:
            self.logger.error(f'Failed to parse JSON response: {e}')
            self.logger.error(f'Response text: {response.text[:200]}...')
        except Exception as e:
            self.logger.error(f'Error processing response: {e}')
            import traceback
            self.logger.error(traceback.format_exc())

# Run the spider if script is executed directly
if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(BeamsShopSpider)
    process.start()
