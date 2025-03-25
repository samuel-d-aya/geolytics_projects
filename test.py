import scrapy
import json

class PanarottisSpider(scrapy.Spider):
    name = 'panarottis'
    allowed_domains = ['panarottis.com']
    
    # The API endpoint we'll be querying
    start_urls = ['https://www.panarottis.com/api/gostore']
    
    def start_requests(self):
        """
        Override the start_requests method to use POST instead of GET
        """
        for url in self.start_urls:
            # You can customize the request payload based on your needs
            payload = {
                # Add request parameters here if needed
                # For example: "storeId": "123", "category": "pizza", etc.
            }
            
            # Set headers to mimic a browser request
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Origin': 'https://www.panarottis.com',
                'Referer': 'https://www.panarottis.com/',
            }
            
            yield scrapy.Request(
                url=url,
                method='POST',
                headers=headers,
                body=json.dumps(payload),
                callback=self.parse
            )
    
    def parse(self, response):
        """
        Parse the JSON response from the API
        """
        try:
            # Parse the JSON response
            data = json.loads(response.text)
            
            # Process and yield the data
            yield {
                'response_data': data,
                'status': response.status,
                'url': response.url
            }
            
            # If the API returns a list of items, you might want to process each item
            # For example:
            if isinstance(data, list):
                for item in data:
                    yield {
                        'item_data': item,
                    }
            elif isinstance(data, dict):
                # If there's a specific data structure in the response
                # For example, if the response has a 'stores' or 'menu' key
                for key, value in data.items():
                    yield {
                        'key': key,
                        'value': value
                    }
            
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse JSON from response: {response.text[:100]}...")
            
    def save_to_file(self, data, filename='panarottis_data.json'):
        """
        Utility method to save scraped data to a file
        """
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
            
# To run this spider from the command line:
# scrapy runspider panarottis_spider.py -o panarottis_data.json