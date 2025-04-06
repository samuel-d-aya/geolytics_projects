import scrapy
import json
import datetime

class NationalTrustSpider(scrapy.Spider):
    name = 'nationaltrust'
    allowed_domains = ['nationaltrust.org.uk']
    start_urls = [
        'https://www.nationaltrust.org.uk/api/search/places?cmsRegion=sussex&query=&placeAgg=region&lang=en&publicationChannel=NATIONAL_TRUST_ORG_UK&maxPlaceResults=1000&maxLocationPageResults=0'
    ]

    # Custom settings to add headers like a real browser
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 2,  # Add delay between requests to avoid being blocked
        'RETRY_TIMES': 3,     # Retry failed requests
        'COOKIES_ENABLED': True,  # Enable cookies
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
        
        # Print raw response for debugging
        self.logger.info(f"Response headers: {response.headers}")
        self.logger.info(f"Response body (first 200 chars): {response.text[:200] if response.text else 'Empty response'}")
        
        # Check if the response is successful (status code 200)
        if response.status != 200:
            self.logger.error(f"Failed to fetch data: Status code {response.status}")
            return
        
        # Check if response body is empty
        if not response.text:
            self.logger.error("Empty response received")
            return
        
        # Attempt to parse the response JSON
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            self.logger.error(f"Raw response: {response.text[:500]}...")  # Log part of the raw response
            return

        # Extract places from the response
        places = data.get('multiMatch', {}).get('aggregations', {}).get('aggregations', {}).get('placesOutsideLocus', {}).get('summaries', [])
        
        if not places:
            self.logger.warning("No places found in response")
            # Try alternative path in case JSON structure changed
            places = data.get('aggregations', {}).get('placesOutsideLocus', {}).get('summaries', [])
            if not places:
                self.logger.error("Could not find places in response using alternative path either")
                return

        # Count total places for logging
        self.logger.info(f"Found {len(places)} places to process")
        
        for place in places:
            # Extract necessary fields from the JSON response
            name = place.get('title')
            place_id = place.get('id', {}).get('value')
            lat = place.get('location', {}).get('lat')
            lon = place.get('location', {}).get('lon')
            
            # Extract day opening status
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
                # If no website URL, yield with the data we have
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
            # Return partial data if website fetch fails
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
        
        # Extract full address - try different selectors if needed
        address_full = response.css('#accordion-item-body--place-contact > div > section > div > div > div > div > address > p::text').get()
        if not address_full:
            # Try alternative selector
            address_full = response.css('address p::text').get()
        
        # Extract phone number href - try different selectors if needed
        phone_href = response.css('#accordion-item-body--place-contact > div > section > div > div > div > div > address > div.GetInTouchstyle__TelWrapper-sc-1vc6bjb-2.ckPoSK > a::attr(href)').get()
        if not phone_href:
            # Try alternative selector
            phone_href = response.css('address div[class*="TelWrapper"] a::attr(href)').get()
        
        # Clean up phone number by removing 'tel:'
        phone = phone_href.replace('tel:', '') if phone_href else None
        
        # Try to extract postcode and city from the full address
        post_code = city = None
        if address_full:
            address_parts = address_full.split(',')
            if len(address_parts) > 1:
                city = address_parts[-2].strip() if len(address_parts) >= 2 else None
                post_code = address_parts[-1].strip()

        # Create the complete item with all data
        result = {
            'name': kwargs.get('name'),
            'ref': kwargs.get('ref'),
            'lat': kwargs.get('lat'),
            'lon': kwargs.get('lon'),
            'day_opening_status': kwargs.get('day_opening_status'),
            'website': kwargs.get('website_url'),
            'address_full': address_full,
            'post_code': post_code,
            'city': city,
            'extras': {
                "brand": "Nationaltrust",
                "fascia": "Nationaltrust",
                "category": "Food & Beverage", 
                "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                "lat_lon_source": "Third-party",
            },
            'phone': phone,
            'state': None
        }
        
        # Yield the complete item
        yield result