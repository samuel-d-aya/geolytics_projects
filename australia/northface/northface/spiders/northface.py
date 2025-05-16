import scrapy
import json
import html
from scrapy.selector import Selector


class StoreSpider(scrapy.Spider):
    name = "northface"
    start_urls = ['https://thenorthface.com.au/stores']  # Replace with actual URL

    def parse(self, response):
        # Extract the raw HTML attribute
        raw_data = response.xpath('//div[@class="jumbotron map-canvas"]/@data-locations').get()

        # Unescape HTML entities (e.g. &quot;)
        unescaped_data = html.unescape(raw_data)

        # Parse JSON
        store_list = json.loads(unescaped_data)

        for store in store_list:
            # Extract data from infoWindowHtml using Selector
            selector = Selector(text=store['infoWindowHtml'])
            
            store_id = selector.xpath('//div[@class="store-details"]/@data-store-id').get()
            store_name = selector.xpath('//div[@class="store-name"]/a/text()').get()
            address = selector.xpath('//address/a/text()').getall()
            address = ' '.join([line.strip() for line in address if line.strip()])

            yield {
                'latitude': store.get('latitude'),
                'longitude': store.get('longitude'),
                'store_id': store_id,
                'store_name': store_name,
                'address': address
            }
