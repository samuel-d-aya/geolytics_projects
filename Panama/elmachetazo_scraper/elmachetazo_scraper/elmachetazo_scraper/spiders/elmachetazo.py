import re
import datetime
import scrapy
from scrapy_playwright.page import PageMethod
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


class ElmachetazoSpider(scrapy.Spider):
    name = "elmachetazo"
    allowed_domains = ["www.elmachetazo.com"]
    start_urls = ["https://www.elmachetazo.com/mapa-tiendas"]
    geolocator = Nominatim(user_agent=name)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                    ],
                },
                callback=self.parse,
            )

    def parse(self, response):
        stores = response.css(".elmachetazo-store-maps-custom-0-x-StoreInMapItem__item")

        for store in stores:
            print(
                f"\n\n{' '.join(store.css('div:last-child > div::text').getall()[2:])}\n\n"
            )
            
            address = store.css("div:last-child > div:first-child::text").get()
            city = store.css("div:first-child > span:first-child::text").get()
            
            # Try to geocode with address and city/country for better results
            location = self.geocode_address(f"{address}")
            
            # Default lat/lon values if geocoding fails
            lat = None
            lon = None
            ref = None
            
            if location:
                lat = location.latitude
                lon = location.longitude
                ref = f"{lat}-{lon}"
            else:
                # Generate a unique reference even without coordinates
                ref = f"elmachetazo-{city}-{re.sub(r'[^\w]', '', address)}"
            
            yield {
                "addr_full": address,
                "brand": "Elmachetazo",
                "city": city,
                "country": "Panama",
                "extras": {
                    "brand": "Elmachetazo",  # Fixed typo in brand name
                    "fascia": "Elmachetazo",  # Fixed typo
                    "category": "Filling Station",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party" if location else None,
                },
                "lat": lat,
                "lon": lon,
                "name": f"Elmachetazo {city}",  # Fixed typo in name
                "opening_hours": self.parse_opening_hours(
                    " ".join(store.css("div:last-child > div::text").getall()[2:])
                ),
                "phone": None,
                "postcode": None,
                "ref": ref,
                "state": None,
                "website": None,
            }

    def geocode_address(self, address):
        """Try to geocode an address with error handling and retries."""
        try:
            # First attempt
            location = self.geolocator.geocode(address, timeout=10)
            if location:
                return location
                
            # If exact address fails, try a simpler version
            simplified = re.sub(r'^(.*?),', '', address).strip()
            if simplified != address:
                location = self.geolocator.geocode(simplified, timeout=10)
                if location:
                    return location
                    
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            self.logger.error(f"Geocoding error for {address}: {e}")
            # Try one more time with a longer timeout
            try:
                return self.geolocator.geocode(address, timeout=20)
            except Exception as e2:
                self.logger.error(f"Second geocoding attempt failed for {address}: {e2}")
                return None
        except Exception as e:
            self.logger.error(f"Unexpected geocoding error for {address}: {e}")
            return None

    def parse_opening_hours(self, text):
        days_map = {
            "lunes": "Mon",
            "martes": "Tue",
            "miércoles": "Wed",
            "jueves": "Thu",
            "viernes": "Fri",
            "sábado": "Sat",
            "domingo": "Sun",
        }

        opening_hours = {}

        if "24 horas" in text.lower():
            return {day: "24 hours" for day in days_map.values()}

        patterns = [
            (
                r"Lunes a Sábado:\s*([\d:apm\s-]+)",
                ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
            ),
            (r"Domingos?:\s*([\d:apm\s-]+)", ["Sun"]),
        ]

        for pattern, days in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                time_range = match.group(1).strip()
                open_time, close_time = time_range.split(" - ")
                open_time = self.convert_to_24h(open_time)
                close_time = self.convert_to_24h(close_time)

                for day in days:
                    opening_hours[day] = f"{open_time}-{close_time}"

        return opening_hours

    def convert_to_24h(self, time_str):
        """Convert '6:00 am' format to 24-hour '06:00'."""
        match = re.match(r"(\d{1,2}):?(\d{0,2})?\s*(am|pm)", time_str, re.IGNORECASE)
        if match:
            hour, minute, period = match.groups()
            hour = int(hour)
            minute = minute if minute else "00"

            if period.lower() == "pm" and hour != 12:
                hour += 12
            elif period.lower() == "am" and hour == 12:
                hour = 0

            return f"{hour:02}:{minute}"

        return time_str