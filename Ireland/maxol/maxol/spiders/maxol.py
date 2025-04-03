import scrapy
import json
import datetime
from urllib.parse import urlencode

class MaxolSpider(scrapy.Spider):
    name = "maxol"
    
    # The base URL without query parameters
    base_url = "https://cdn.yextapis.com/v2/accounts/me/answers/vertical/query"
    
    # API key and other static parameters
    params = {
        "experienceKey": "maxol-station-finder",
        "api_key": "3652290fc55da954d9da84ed7947c845",
        "v": "20220511",
        "version": "PRODUCTION",
        "locale": "en",
        "input": "",
        "location": "53.7798,-7.3055",
        "verticalKey": "locations",
        "limit": 10,
        "retrieveFacets": "true",
        "facetFilters": '{"c_pagesFiltersFuels":[],"c_servicesContent.name":[],"c_foodList":[]}',
        "skipSpellCheck": "false",
        "sessionTrackingEnabled": "false",
        "sortBys": "[]",
        "source": "STANDARD"
    }
    
    # Day mapping for formatting opening hours
    day_mapping = {
        "monday": "Mon",
        "tuesday": "Tue",
        "wednesday": "Wed",
        "thursday": "Thu",
        "friday": "Fri",
        "saturday": "Sat",
        "sunday": "Sun"
    }
    
    def format_opening_hours(self, hours):
        
        if not hours:
            return {}
            
        formatted_hours = {}
        
        for day_full, day_info in hours.items():
            day_short = self.day_mapping.get(day_full)
            if not day_short:
                continue
                
            if "openIntervals" in day_info and day_info["openIntervals"]:
                interval = day_info["openIntervals"][0]  # Take the first interval
                formatted_hours[day_short] = f"{interval['start']}-{interval['end']}"
            else:
                formatted_hours[day_short] = "Closed"
                
        return formatted_hours

    def start_requests(self):
        for offset in range(0, 250, 10):  # offset will run from 0 to 240 (in increments of 10)
            
            current_params = self.params.copy()
            current_params["offset"] = offset
            
            # Construct the full URL with query parameters
            url = f"{self.base_url}?{urlencode(current_params)}"
            
            self.logger.info(f"Requesting URL: {url}")
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                cb_kwargs={'offset': offset}
            )

    def parse(self, response, offset):
        try:
            data = json.loads(response.text)
            results = data.get("response", {}).get("results", [])
            
            self.logger.info(f"Received {len(results)} results for offset {offset}")          
            
            
            for result in results:
                location = result.get("data", {})
                address = location.get("address", {})
                
                # Format the opening hours
                raw_hours = location.get("hours")
                formatted_hours = self.format_opening_hours(raw_hours)  
                
                yield {
                    "addr_full": f"{address.get("line1", '')} {address.get("postalCode", '')} {address.get("city", '')}",
                    "city": address.get("city"),
                    "country": address.get("countryCode"),
                    "brand": "Maxol",
                    "extras": {
                        "brand": "Maxol",
                        "fascia": "Maxol Service Station",
                        "category": "Service Station",
                        "edit_date": datetime.datetime.now().strftime('%Y%m%d'),
                        "lat_lon_source": "website",
                    },
                    "lat": location.get("yextDisplayCoordinate", {}).get("latitude"),
                    "lon": location.get("yextDisplayCoordinate", {}).get("longitude"),
                    "opening_hours": formatted_hours,
                    "phone": location.get("mainPhone"),
                    "ref": location.get("id"),
                    "postcode": address.get("postalCode"),
                    "name": location.get("name"),
                    "state": address.get("subLocality"),
                    "website": "https://stations.maxol.ie/",
                }
                
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse JSON for offset {offset}. Response: {response.text[:100]}...")