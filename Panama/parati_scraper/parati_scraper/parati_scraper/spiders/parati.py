import re
import datetime
import scrapy


class ParatiSpider(scrapy.Spider):
    name = "parati"
    allowed_domains = ["www.arrochaparati.com"]
    start_urls = ["https://www.arrochaparati.com/es/tiendas-app"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_store_url,
            )

    def parse_store_url(self, response):

        stores = response.css(
            ".tienda-item > div > div > div > div:nth-child(3) > a::attr(href)"
        ).getall()

        for store in stores:
            store_url = response.urljoin(store)
            yield response.follow(
                store_url,
                callback=self.parse_store_details,
            )

    def parse_store_details(self, response):

        lon_lat = (
            response.css(
                ".tienda-detail > div > div > div > div:nth-child(2) > div:nth-child(3) > a::attr(href)"
            )
            .get()
            .split("q=")[1]
            .split(",")
        )

        yield {
            "addr_full": response.css(
                ".tienda-detail > div > div > div > div:nth-child(2) > div:nth-child(2) > p > b::text"
            ).get(),
            "brand": "Arrocha Parati",
            "city": response.css("body > div.wrap > main > section.block_list_288_2.block-list.block-list-tienda.block-list-tienda-app.block-catalog.mb-0 > div > div > div::text").get(),
            "country": "Panama",
            "extras": {
                "brand": " Arrocha Parati",
                "fascia": "Arrocha Parati",
                "category": "Pharmacy",
                "edit_date": str(datetime.datetime.now().date()),
                "lat_lon_source": "Website",
            },
            "lat": lon_lat[0],
            "lon": lon_lat[1],
            "name": response.css("h1::text").get(),
            "opening_hours": self.parse_opening_hours(
                response.css(
                    ".tienda-detail > div > div > div > div:nth-child(2) > div::text"
                ).getall()
            ),
            "phone": None,
            "postcode": None,
            "ref": "-".join(lon_lat),
            "state": None,
            "website": response.url,
        }

    def parse_opening_hours(self, opening_hours):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        opening_hours_dict = {}
        for day in days:
            opening_hours_dict[day] = re.sub(r"\s+|am|pm", "", opening_hours[0])

        return {"opening_hours": opening_hours_dict}

