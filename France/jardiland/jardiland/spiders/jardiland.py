import scrapy
import json

class JardilandSpider(scrapy.Spider):
    name = "jardiland"
    start_urls = [
        "https://uberall.com/api/storefinders/rwiQToDdMrVSqdKnYA0X3wMpORnyUW/locations/all?v=20230110&language=fr&fieldMask=id&fieldMask=identifier&fieldMask=googlePlaceId&fieldMask=lat&fieldMask=lng&fieldMask=name&fieldMask=country&fieldMask=city&fieldMask=province&fieldMask=streetAndNumber&fieldMask=zip&fieldMask=businessId&fieldMask=addressExtra&"
    ]
    
    location_data = {}

    def parse(self, response):
        self.logger.info(f"Processing first URL: {response.url}")
        try:
            data = json.loads(response.text)
            locations = data.get('response', {}).get('locations', [])
            
            if not locations:
                self.logger.error(f"No locations found in response: {data}")
                return
                
            self.logger.info(f"Found {len(locations)} locations")
            
            # Store basic location data in a dictionary keyed by ID
            for location in locations:
                location_id = location.get('id')
                if location_id:
                    self.location_data[location_id] = {
                        'lat': location.get('lat'),
                        'long': location.get('lng'),
                        'name': location.get('name'),
                        'address': location.get('streetAndNumber'),
                        'city': location.get('city'),
                        'state': location.get('province'),
                        'postcode': location.get('zip'),
                        'country': location.get('country'),
                        'ref': location_id
                    }
            
            # Collect location IDs
            location_ids = list(self.location_data.keys())
            self.logger.info(f"Collected {len(location_ids)} location IDs")
            
            # Make batched requests to avoid URL length limitations
            batch_size = 20 
            for i in range(0, len(location_ids), batch_size):
                batch = location_ids[i:i+batch_size]
                second_url = "https://uberall.com/api/storefinders/rwiQToDdMrVSqdKnYA0X3wMpORnyUW/locations?v=20230110&language=fr"
                
                # Add location IDs for this batch
                for location_id in batch:
                    second_url += f"&locationIds={location_id}"
                
                field_masks = [
                    "id",  
                    "callToActions", 
                    "futureOpeningDate", 
                    "openingHours", 
                    "openNow", 
                    "nextOpen",
                    "phone", 
                    "photos", 
                    "specialOpeningHours", 
                    "streetAndNumber", 
                    "temporarilyClosedInfo"
                ]
                for field_mask in field_masks:
                    second_url += f"&fieldMask={field_mask}"
                
                self.logger.info(f"Making batch request {i//batch_size + 1} with {len(batch)} IDs.")
                
                yield scrapy.Request(
                    url=second_url, 
                    callback=self.parse_additional_info,
                    errback=self.handle_error,
                    meta={'batch_ids': batch}
                )
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
        except Exception as e:
            self.logger.error(f"Error in parse: {e}")

    def parse_additional_info(self, response):
        self.logger.info(f"Processing second URL: {response.url}")
        batch_ids = response.meta.get('batch_ids', [])
        
        try:
            data = json.loads(response.text)
            
            status = data.get('status')
            self.logger.info(f"Second request status: {status}")
            
            locations = data.get('response', {}).get('locations', [])
            
            if not locations:
                self.logger.error(f"No locations found in additional info.")
                for location_id in batch_ids:
                    if location_id in self.location_data:
                        yield self.location_data[location_id]
                return
                
            self.logger.info(f"Found {len(locations)} locations in additional info")
            
            # Process locations with additional info
            processed_ids = set()
            for location in locations:
                location_id = location.get('id')
                
                if location_id and location_id in self.location_data:
                    combined_data = self.location_data[location_id].copy()
                    
                    # additional data
                    additional_data = {
                        'phone': location.get('phone'),
                        'openingHours': location.get('openingHours'),
                        'callToActions': location.get('callToActions')
                    }
                    
                    combined_data.update(additional_data)
                    yield combined_data
                    processed_ids.add(location_id)
            
            # Yield basic data for IDs in this batch that weren't in the response
            missing_ids = set(batch_ids) - processed_ids
            if missing_ids:
                self.logger.warning(f"IDs not found in second response: {missing_ids}")
                for location_id in missing_ids:
                    if location_id in self.location_data:
                        yield self.location_data[location_id]
                    
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in additional info: {e}")
            # Yield basic data on JSON error
            for location_id in batch_ids:
                if location_id in self.location_data:
                    yield self.location_data[location_id]
        except Exception as e:
            self.logger.error(f"Error in parse_additional_info: {e}")
            # Yield basic data on any error
            for location_id in batch_ids:
                if location_id in self.location_data:
                    yield self.location_data[location_id]
    
    def handle_error(self, failure):
        self.logger.error(f"Request failed: {failure.value}")
        # Try to get batch IDs from the failed request
        batch_ids = failure.request.meta.get('batch_ids', [])
        # Yield basic data for these IDs
        for location_id in batch_ids:
            if location_id in self.location_data:
                yield self.location_data[location_id]