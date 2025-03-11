import scrapy
import json
import datetime

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
                        'address': location.get('streetAndNumber'),
                        'city': location.get('city'),
                        'postcode': location.get('zip'),
                        'country': location.get('country'),
                        "extras": {
                            'Brand': "Jardiland",
                            'fascia': "Jardiland",
                            "category": "Sports",
                            "edit_date": datetime.datetime.now().strftime('%Y%m%d'),
                            "lat_lon_source": "Third Party",
                        },
                        'lat': location.get('lat'),
                        'long': location.get('lng'),
                        'name': location.get('name'),
                        'ref': location_id,
                        'state': location.get('province')
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
                    
                    call_to_actions = location.get('callToActions', [])
                    
                    # Additional data
                    additional_data = {
                        'phone': location.get('phone'),
                        'website': call_to_actions[0].get('url')
                    }
                    
                    # Handle opening hours
                    opening_hours = location.get('openingHours', [])
                    formatted_opening_hours = {}
                    day_mapping = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
                    
                    for day_data in opening_hours:
                        day_of_week = day_data.get('dayOfWeek')
                        time_slots = []
                        
                        # Check if the store has opening hours for the day
                        if 'from1' in day_data and 'to1' in day_data:
                            time_slots.append(f"{day_data['from1']}-{day_data['to1']}")
                        if 'from2' in day_data and 'to2' in day_data:
                            time_slots.append(f"{day_data['from2']}-{day_data['to2']}")
                        
                        # If the store is closed on that day, set the opening hours to "Closed"
                        if 'closed' in day_data and day_data['closed']:
                            formatted_opening_hours[day_mapping.get(day_of_week, "")] = "Closed"
                        elif time_slots:
                            formatted_opening_hours[day_mapping.get(day_of_week, "")] = ", ".join(time_slots)
                        else:
                            # If no hours are available, leave it empty
                            formatted_opening_hours[day_mapping.get(day_of_week, "")] = ""
                    
                    # Add formatted opening hours to additional data
                    additional_data['opening_hours'] = {"opening_hours":formatted_opening_hours}
                    
                    # Combine the basic data and additional data
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