import scrapy
import json
import datetime
import re

class NationalTrustSpider(scrapy.Spider):
    name = 'nationaltrust'
    allowed_domains = ['nationaltrust.org.uk']
    start_urls = [
        'https://www.nationaltrust.org.uk/api/search/places?cmsRegion=sussex&query=&placeAgg=region&lang=en&publicationChannel=NATIONAL_TRUST_ORG_UK&maxPlaceResults=1000&maxLocationPageResults=0'
    ]

    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 2,  
        'RETRY_TIMES': 3,     
        'COOKIES_ENABLED': True,  
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers={
                    'Accept': 'application/json',
                    'Referer': 'https://www.nationaltrust.org.uk/',
                    'Content-Type': 'application/json'
                },
                meta={'dont_redirect': True, 'handle_httpstatus_list': [302, 403, 404, 500]}
            )

    def parse(self, response):
        self.logger.info(f"Response status: {response.status}")
        
        
        self.logger.info(f"Response headers: {response.headers}")
        self.logger.info(f"Response body (first 200 chars): {response.text[:200] if response.text else 'Empty response'}")
        
        
        if response.status != 200:
            self.logger.error(f"Failed to fetch data: Status code {response.status}")
            return
        
        if not response.text:
            self.logger.error("Empty response received")
            return
        
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            self.logger.error(f"Raw response: {response.text[:500]}...")  
            return

        # Extract places from the response
        places = data.get('multiMatch', {}).get('aggregations', {}).get('aggregations', {}).get('placesOutsideLocus', {}).get('summaries', [])
        
        if not places:
            self.logger.warning("No places found in response")
            
            places = data.get('aggregations', {}).get('placesOutsideLocus', {}).get('summaries', [])
            if not places:
                self.logger.error("Could not find places in response using alternative path either")
                return

        # Count total places
        self.logger.info(f"Found {len(places)} places to process")
        
        for place in places:
        
            name = place.get('title')
            place_id = place.get('id', {}).get('value')
            lat = place.get('location', {}).get('lat')
            lon = place.get('location', {}).get('lon')
            day_status = place.get('dayOpeningStatus', [])
            day_opening_status = day_status[0]['openingTimeStatus'] if day_status else None
            
            website_url = place.get('websiteUrl')

            # Only follow the website URL to extract more details
            if website_url:
                self.logger.info(f"Following URL for {name}: {website_url}")
                yield scrapy.Request(
                    url=website_url,
                    callback=self.parse_website,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Referer': 'https://www.nationaltrust.org.uk/'
                    },
                    cb_kwargs={
                        'name': name,
                        'ref': place_id,
                        'lat': lat,
                        'lon': lon,
                        'day_opening_status': day_opening_status,
                        'website_url': website_url
                    }
                )
            else:
                self.logger.warning(f"No website URL for {name}, yielding with partial data")
                yield {
                    'name': name,
                    'ref': place_id,
                    'lat': lat,
                    'lon': lon,
                    'day_opening_status': day_opening_status,
                    'website_url': None,
                    'address_full': None,
                    'post_code': None,
                    'city': None,
                    'extras': {
                        "brand": "Nationaltrust",
                        "fascia": "Nationaltrust",
                        "category": "Food & Beverage",
                        "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                        "lat_lon_source": "Third-party",
                    },
                    'phone': None,
                    'state': None
                }
    
    def parse_website(self, response, **kwargs):
        self.logger.info(f"Processing website for: {kwargs.get('name')} (Status: {response.status})")
        
        if response.status != 200:
            self.logger.error(f"Failed to fetch website data for {kwargs.get('name')}: Status code {response.status}")
            return {
                'name': kwargs.get('name'),
                'ref': kwargs.get('ref'),
                'lat': kwargs.get('lat'),
                'lon': kwargs.get('lon'),
                'day_opening_status': kwargs.get('day_opening_status'),
                'website_url': kwargs.get('website_url'),
                'extras': {
                    "brand": "Nationaltrust",
                    "fascia": "Nationaltrust",
                    "category": "Food & Beverage", 
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Third-party",
                }
            }
        
        # Extract full address 
        address_full = response.css('#accordion-item-body--place-contact > div > section > div > div > div > div > address > p::text').get()
        if not address_full:
            # Try alternative selector
            address_full = response.css('address p::text').get()
        
        # Extract phone number href 
        phone_href = response.css('#accordion-item-body--place-contact > div > section > div > div > div > div > address > div.GetInTouchstyle__TelWrapper-sc-1vc6bjb-2.ckPoSK > a::attr(href)').get()
        if not phone_href:
            # Try alternative selector
            phone_href = response.css('address div[class*="TelWrapper"] a::attr(href)').get()
        
        # Clean up phone number
        phone = phone_href.replace('tel:', '') if phone_href else None
        
        # Try to extract postcode and city from the full address
        post_code = city = None
        if address_full:
            postcode_match = re.search(r'\b([A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2})\b', address_full)
            if postcode_match:
                post_code = postcode_match.group(0)

            address_parts = address_full.split(',')
            if len(address_parts) > 1:
                city = address_parts[-2].strip() if len(address_parts) >= 2 else None

        result = {
            'address_full': address_full,
            'city': city,
            'country': 'United Kingdom',
            'address_full': address_full,
            'brand': 'Nationaltrust',
            'extras': {
                "brand": "Nationaltrust",
                "fascia": "Nationaltrust",
                "category": "National sites", 
                "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                "lat_lon_source": "Third-party",
            },
            'lat': kwargs.get('lat'),
            'lon': kwargs.get('lon'),
            'day_opening_status': kwargs.get('day_opening_status'),
            'phone': phone,
            'ref': kwargs.get('ref'),
            'post_code': post_code,
            'name': kwargs.get('name'),
            'state': None,
            'website': kwargs.get('website_url')
        }
        
        yield result