import re
import datetime
import scrapy
from geopy.geocoders import Nominatim
import time


class Super99Spider(scrapy.Spider):
    name = "super99"
    allowed_domains = ["www.super99.com"]
    start_urls = ["https://www.super99.com/nuestras-sucursales"]
    
    def __init__(self, *args, **kwargs):
        super(Super99Spider, self).__init__(*args, **kwargs)
        self.geolocator = Nominatim(user_agent="super99_spider")

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        regions = response.css(".our-branches-collapsible")
        for region in regions:
            stores = region.css(".our-branch-info")

            for store in stores:
                city = region.css(".our-branches-title-collapsible > p::text").get()
                addr_full = store.css(".our-branch-info__first-column")[0].css("div > p:last-child::text").get()
                brand = store.css(".our-branch-info__first-column")[0].css("div > p:first-child::text").get()
                coord = store.css(".first-button > a::attr(href)").get()
                
                # Extract lat and lon from map link or use geocoding
                lat, lon = self.extract_coordinates(coord, addr_full, city)
                
                yield {
                    "addr_full": addr_full,
                    "brand": brand,
                    "city": city,
                    "country": "Panama",
                    "extras": {
                        "brand": brand,
                        "fascia": brand,
                        "category": "Filling Station",
                        "edit_date": datetime.datetime.now().strftime('%Y%m%d'),
                        "lat_lon_source": "Website" if coord and "@" in coord else "Geocoded",
                    },
                    "lat": lat,
                    "lon": lon,
                    "name": f"{brand} {addr_full}",
                    "opening_hours": self.parse_opening_hours(
                        store.css(
                            ".our-branch-info__second-column > div > p::text"
                        ).getall()[1:]
                    ),
                    "phone": store.css(
                        ".our-branch-info__second-column > div > p::text"
                    )
                    .get()
                    .split(":")[1].strip(),
                    "postcode": None,
                    "ref": f"{lat},{lon}" if lat and lon else None,
                    "state": None,
                    "website": store.css(".last-button > a::attr(href)").get(),
                }

    def extract_coordinates(self, coord_url, address, city):
        """Extract coordinates from map URL or geocode using address"""
        # Try to extract from map URL first
        if coord_url and "@" in coord_url:
            try:
                
                parts = coord_url.split("@")[1].split(",")
                if len(parts) >= 2:
                    return parts[0], parts[1]
            except (IndexError, ValueError):
                self.logger.warning(f"Failed to parse coordinates from URL: {coord_url}")
        
       
        try:
            # Format the address for geocoding
            geocode_address = f"{address}, {city}, Panama"
            self.logger.info(f"Geocoding address: {geocode_address}")
            
            # Add a small delay to avoid hitting rate limits
            time.sleep(1)
            
            # Perform geocoding
            location = self.geolocator.geocode(geocode_address)
            
            if location:
                return str(location.latitude), str(location.longitude)
            else:
                self.logger.warning(f"Geocoding failed for address: {geocode_address}")
                return None, None
        except Exception as e:
            self.logger.error(f"Geocoding error for {address}: {str(e)}")
            return None, None

    def parse_opening_hours(self, opening_hour_list):
        days_map = {
            "lunes": "Mon",
            "martes": "Tue",
            "miércoles": "Wed",
            "jueves": "Thu",
            "viernes": "Fri",
            "sábado": "Sat",
            "domingo": "Sun",
            "sábados": "Sat",
            "domingos": "Sun",
        }

        opening_hours = {}
        for line in opening_hour_list:
            match = re.match(
                r"([\w\sáéíóú]+) (\d{1,2}:\d{2} [apm\.]+) - (\d{1,2}:\d{2} [apm\.]+)",
                line.strip(),
            )
            if match:
                days_part, open_time, close_time = match.groups()
                open_time = open_time.replace(" ", "")  # Normalize time format
                close_time = close_time.replace(" ", "")

                days_part = days_part.lower().replace("\xa0", "")

                if " a " in days_part:
                    day1, day2 = days_part.split(" a ")
                    day_keys = list(days_map.keys())
                    start_idx, end_idx = day_keys.index(day1), day_keys.index(day2)

                    for i in range(start_idx, end_idx + 1):
                        opening_hours[days_map[day_keys[i]]] = (
                            f"{open_time}-{close_time}"
                        )

                elif " y " in days_part:
                    days = days_part.split(" y ")
                    for day in days:
                        opening_hours[days_map[day]] = f"{open_time}-{close_time}"

                else:
                    opening_hours[days_map[days_part]] = f"{open_time}-{close_time}"

        return {"opening_hours": opening_hours}