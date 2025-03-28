import datetime
import scrapy
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

class MoschSpider(scrapy.Spider):
    name = "mosch"
    allowed_domains = ["www.moschmosch.com"]
    start_urls = ["https://www.moschmosch.com/restaurants.php"]
    geolocator = Nominatim(user_agent=name)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_store_url)

    def parse_store_url(self, response):
        store_urls = response.css(
            ".grid-post-meta > p:nth-child(3) > a::attr(href)"
        ).getall()
        store_urls.append(
            response.css(".grid-post-meta > p:nth-of-type(1) > a::attr(href)").get()
        )

        for url in store_urls:
            store_url = f"https://www.moschmosch.com/{url}"
            yield response.follow(url=store_url, callback=self.parse)

    def parse(self, response):
        full_address = response.css(
            ".container > div > div:nth-child(2) > p:nth-child(2)::text"
        ).getall()

        open_hour_list = (
            response.css(
                ".container > div > div:nth-child(2) > p:nth-of-type(2) > strong::text"
            ).getall()
            if response.css(
                ".container > div > div:nth-child(2) > p:nth-of-type(2) > strong::text"
            ).getall()
            else response.css(
                ".container > div > div:nth-child(2) > p:nth-of-type(2)::text"
            ).getall()
        )
        postal_city = full_address[1] if len(full_address) < 5 else full_address[2]
        lat, lon = self.geocode_address(postal_city)

        yield {
            "addr_full": full_address[0],
            "brand": "Mosch Mosch",
            "city": postal_city.split()[1],
            "country": "Germany",
            "extras": {
                "brand": "Mosch Mosh",
                "fascia": "Mosch Mosch",
                "category": "Food and Beverage",
                "edit_date": str(datetime.datetime.now().date()),
                "lat_lon_source": "Third Party",
            },
            "lat": lat,
            "lon": lon,
            "name": response.css(
                ".container > div > div:nth-child(2) > h1::text"
            ).get(),
            "opening_hours": self.parse_opening_hours(open_hour_list),
            "phone": response.css(
                ".container > div > div:nth-child(2) > p > a::text"
            ).get(),
            "postcode": full_address[1].split()[0],
            "ref": f"{lat}-{lon}",
            "state": None,
            "website": response.url,
        }

    def geocode_address(self, address):
        """Geocode the address and return latitude and longitude."""
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

    def parse_opening_hours(self, hours_list):
        day_map = {
            "Mo": "Mon",
            "Di": "Tue",
            "Mi": "Wed",
            "Do": "Thu",
            "Fr": "Fri",
            "Sa": "Sat",
            "So": "Sun",
        }

        result = {}

        cleaned_input = " ".join(line.strip() for line in hours_list if line.strip())
        if not cleaned_input:
            return result

        entries = [entry.strip() for entry in cleaned_input.split(",") if entry.strip()]

        for entry in entries:
            match = re.match(
                r"([A-Za-z\s+:&-]+)?\s*(\d{1,2}(?:[.:]\d{2})?)\s*-\s*(\d{1,2}(?:[.:]\d{2})?)\s*Uhr",
                entry,
                re.IGNORECASE,
            )
            if not match:
                continue

            days_part, start_time, end_time = match.groups()

            start_time = start_time.replace(".", ":").replace(" ", "")
            end_time = end_time.replace(".", ":").replace(" ", "")
            if ":" not in start_time:
                start_time += ":00"
            if ":" not in end_time:
                end_time += ":00"
            time_range = f"{start_time} - {end_time}"

            if not days_part:
                days_part = entry.split()[0]
            days_part = days_part.replace(" ", "").replace(":", "")

            if "-" in days_part:
                start_day, end_day = days_part.split("-")
                try:
                    start_idx = list(day_map.keys()).index(start_day)
                    end_idx = list(day_map.keys()).index(end_day)

                    for i in range(start_idx, end_idx + 1):
                        day = list(day_map.values())[i]
                        result[day] = time_range
                except ValueError as e:
                    self.logger.error(f"Error parsing day range in: {entry} - {e}")
            elif "+" in days_part or "&" in days_part:
                separator = "+" if "+" in days_part else "&"
                days = days_part.split(separator)
                for day in days:
                    if day in day_map:
                        result[day_map[day]] = time_range
                    else:
                        self.logger.error(f"Ignoring unrecognized day: {day} in {entry}")
            else:
                try:
                    result[day_map[days_part]] = time_range
                except KeyError as e:
                    self.logger.error(f"Error mapping single day in: {entry} - {e}")

        return {"opening_hours": result}
