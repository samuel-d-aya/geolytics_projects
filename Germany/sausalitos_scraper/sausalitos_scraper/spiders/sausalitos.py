import scrapy
import json
import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
import brotli  # For brotli decompression

class SausalitosSpider(scrapy.Spider):
    name = "sausalitos"
    allowed_domains = ["www.sausalitos.de"]
    start_urls = ["https://www.sausalitos.de/uberall-data"]

    custom_headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.7",
        "referer": "https://www.sausalitos.de/standorte",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }
    
    def __init__(self, *args, **kwargs):
        super(SausalitosSpider, self).__init__(*args, **kwargs)
        self.geolocator = Nominatim(user_agent="sausalitos_scraper")

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            headers=self.custom_headers,
            callback=self.parse,
            dont_filter=True
        )

    def geocode_address(self, address):
        try:
            location = self.geolocator.geocode(address, timeout=10)
            time.sleep(1)  # Add delay to avoid rate limits
            if location:
                return location.latitude, location.longitude
            else:
                self.logger.warning(f"Geocoding failed for address: {address}")
                return None, None
        except GeocoderTimedOut:
            self.logger.error(f"Geocoding timed out for address: {address}")
            return None, None
        except Exception as e:
            self.logger.error(f"Geocoding error for address {address}: {e}")
            return None, None

    def parse(self, response):
        """Parse the response manually"""
        try:
            # Check for content encoding - we need to handle brotli compression
            content_encoding = response.headers.get('Content-Encoding', b'').decode('utf-8', 'ignore')
            self.logger.info(f"Response content encoding: {content_encoding}")
            
            # Get response body
            body = response.body
            
            # If response is brotli compressed, decompress it
            if 'br' in content_encoding:
                try:
                    self.logger.info("Detected brotli compression, attempting to decompress")
                    body = brotli.decompress(body)
                except Exception as e:
                    self.logger.error(f"Failed to decompress brotli: {e}")
            
            # Decode and parse JSON
            data = json.loads(body.decode('utf-8', errors='replace'))
            self.logger.info(f"Successfully parsed JSON response with keys: {list(data.keys())}")
            
            if not data.get("locations"):
                self.logger.error("No locations found in response.")
                return

            for location in data["locations"]:
                city = location.get("city", "")
                zipcode = location.get("zip", "")
                address = location.get("streetAndNumber", "")
                location_id = location.get("id", "")
                phone = location.get("phone", "")
                
                full_address = f"{address}, {zipcode} {city}, Germany"
                
                lat, lon = self.geocode_address(full_address)

                # Format opening hours
                opening_hours = {
                        "Mon": " ",
                        "Tue": " ",
                        "Wed": " ",
                        "Thu": " ",
                        "Fri": " ",
                        "Sat": " ",
                        "Sun": " "
                }
                
                for hours in location.get("openingHours", []):
                    day_of_week = hours.get("dayOfWeek")
                    from_time = hours.get("from1", "")
                    to_time = hours.get("to1", "")

                    day_mapping = {
                        1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu",
                        5: "Fri", 6: "Sat", 7: "Sun"
                    }
                    
                    day_str = day_mapping.get(day_of_week, f"Day{day_of_week}")
                    opening_hours[day_str] = f"{from_time}-{to_time}"

                yield {
                    "addr_full": full_address,
                    "city": city,
                    "country": "Germany",
                    "brand": "Sausalitos",
                    "extras": {
                        "brand": "Sausalitos",
                        "fascia": "Sausalitos",
                        "category": "Food & Beverage",
                        "edit_date": datetime.datetime.now().strftime('%Y%m%d'),
                        "lat_lon_source": "Third-party",
                    },
                    "lat": lat,
                    "lon": lon,
                    "opening_hours": {"opening_hours":opening_hours},
                    "phone": phone,
                    "ref": location_id,
                    "postcode": zipcode,
                    "name": f"Sausalitos {city}",
                    "state": None,
                    "website": "https://www.sausalitos.de/standorte",
                    
                }
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            self.logger.error(f"Response body preview: {response.body[:200]}")
        except Exception as e:
            self.logger.error(f"Unexpected error in parse method: {e}")
            self.logger.error(f"Response status: {response.status}")
            self.logger.error(f"Response headers: {response.headers}")