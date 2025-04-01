import scrapy
import json
import datetime
import re

class LosteriaSpider(scrapy.Spider):
    name = "losteria"
    allowed_domains = ["losteria.net"]
    start_urls = ["https://losteria.net/en/restaurants/view/list/?tx_losteriarestaurants_restaurants%5Bfilter%5D%5Bcountry%5D=de"]

    def parse(self, response):
        # Extract restaurant links in Germany
        restaurant_links = response.css('a.single-link.detail::attr(href)').getall()
        for link in restaurant_links:
            if "/en/restaurants/restaurant/" in link:
                full_link = response.urljoin(link)
                yield scrapy.Request(url=full_link, callback=self.parse_restaurant)

    def parse_restaurant(self, response):
        # Extract address block
        address_block = response.css('.address::text').getall()
        
        # Join all elements and clean up spaces, newlines, tabs
        full_address = ' '.join(address_block)
        cleaned_address = re.sub(r'[\s\n\t]+', ' ', full_address).strip()
        
        # Extract components using regex
        # Look for pattern: street address, postal code, city
        match = re.search(r'(.*?),\s*(\d{5})\s+(.*)', cleaned_address)
        
        if match:
            street_address = match.group(1).strip()
            postal_code = match.group(2)
            city = match.group(3).strip()
        else:
            # Fallback if regex doesn't match
            street_address = cleaned_address
            postal_code = None
            city = None
        
        # For the full address without spaces between components
        compact_address = street_address + "," + (postal_code or "") + " " + (city or "")
        
        phone = response.css('.telephone.phone-link::text').get()

        yield {
            'full_address': cleaned_address,
            'compact_address': compact_address,
            'street_address': street_address,
            'city': city,
            'postal_code': postal_code,
            'phone': phone,
        }
