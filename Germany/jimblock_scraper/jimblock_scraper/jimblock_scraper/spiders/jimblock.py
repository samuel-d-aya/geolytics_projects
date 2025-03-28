import scrapy
import datetime
from geopy.geocoders import Nominatim


class JimblockSpider(scrapy.Spider):
    name = "jimblock"
    allowed_domains = ["www.jim-block.de"]
    start_urls = ["https://www.jim-block.de/restaurants/"]
    geolocator = Nominatim(user_agent=name)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_store_url)

    def parse_store_url(self, response):
        store_urls = response.css(".restaurant > h3 > a::attr(href)").getall()

        for url in store_urls:
            store_url = f"https://www.jim-block.de{url}"

            yield response.follow(url=store_url, callback=self.parse_store_details)

    def parse_store_details(self, response):

        full_address = response.css(".restaurant[data-index='0'] > p::text").getall()

        location = self.geolocator.geocode("".join(full_address))

        yield {
            "addr_full": full_address[0],
            "brand": "Jim-block",
            "city": full_address[1].split()[1],
            "country": "Germany",
            "extras": {
                "brand": "Jim-block",
                "fascia": "Jim-block",
                "category": "Food and Beverage",
                "edit_date": str(datetime.datetime.now().date()),
                "lat_lon_source": "Third Party",
            },
            "lat": location.latitude,
            "lon": location.longitude,
            "name": response.css(".textpictures .text-inner h1::text").get(),
            "opening_hours": self.parse_opening_hours(
                response.css(".restaurant[data-index='2'] > p::text").getall()
            ),
            "phone": response.css(".restaurant[data-index='1'] > p > a::text").get(),
            "postcode": full_address[1].split()[0],
            "ref": f"{round(float(location.latitude),2)}-{round(float(location.longitude), 2)}",
            "state": None,
            "website": response.url,
        }

    def parse_opening_hours(self, hour_list):
        self.logger.info(f"This is {hour_list[1]}")

        output = {
            "opening_hours": {
                "mon": hour_list[0]
                .split("Do:")[1]
                .replace("bis", "-")
                .replace("Uhr", ""),
                "tue": hour_list[0]
                .split("Do:")[1]
                .replace("bis", "-")
                .replace("Uhr", ""),
                "wed": hour_list[0]
                .split("Do:")[1]
                .replace("bis", "-")
                .replace("Uhr", ""),
                "thur": hour_list[0]
                .split("Do:")[1]
                .replace("bis", "-")
                .replace("Uhr", ""),
                "fri": hour_list[-1]
                .split("Sa:")[1]
                .replace("bis", "-")
                .replace("Uhr\xa0", ""),
                "sat": hour_list[-1]
                .split("Sa:")[1]
                .replace("Uhr\xa0", "-")
                .replace("Uhr", ""),
                "sun": hour_list[0]
                .split("Do:")[1]
                .replace("bis", "-")
                .replace("Uhr", ""),
            }
        }
        return output
