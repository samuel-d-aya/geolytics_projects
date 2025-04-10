import json
import datetime
import scrapy


class DebonairSpider(scrapy.Spider):
    name = "debonair"
    allowed_domains = ["location.debonairspizza.co.za"]
    start_urls = ["https://location.debonairspizza.co.za/"]

    def start_requests(self):
        for url in self.start_urls:

            yield scrapy.Request(url=url, callback=self.parse_region_url)

    def parse_region_url(self, response):

        region_urls = response.css(".Directory-listLink::attr(href)").getall()

        for url in region_urls:
            region_url = response.urljoin(url)

            yield response.follow(url=region_url, callback=self.parse_store_url)

    def parse_store_url(self, response):

        store_urls = response.css(".Directory-listLink::attr(href)").getall()
        data_count = response.css(".Directory-listLink::attr(data-count)").getall()

        for url, count in zip(store_urls, data_count):

            count = int(count.replace("(", "").replace(")", ""))

            store_url = response.urljoin(url)
            if count == 1:

                yield response.follow(
                    url=store_url,
                    callback=self.parse_store_details,
                )
            else:
                yield response.follow(url=store_url, callback=self.parse_plus_url)

    def parse_plus_url(self, response):

        store_urls = response.css(".Teaser-titleLink::attr(href)").getall()

        for url in store_urls:
            store_url = f"{self.start_urls[0]}{url.replace("../", "")}"
            yield response.follow(url=store_url, callback=self.parse_store_details)

    def parse_store_details(self, response):

        lat = response.css(
            ".Core-address > span > meta:nth-child(1)::attr(content)"
        ).get()
        lon = response.css(
            ".Core-address > span > meta:nth-child(2)::attr(content)"
        ).get()

        yield {
            "addr_full": response.css(
                "#address > meta:nth-child(2)::attr(content)"
            ).get(),
            
            "city": response.css("#address > meta:nth-child(1)::attr(content)").get(),
            "country": "South Africa",
            "brand": response.css(".LocationName-brand::text").get(),
            "extras": {
                "brand": response.css(".LocationName-brand::text").get(),
                "fascia": response.css(".LocationName-brand::text").get(),
                "category": "Food and Beverage",
                "edit_date": str(datetime.datetime.now().date()),
                "lat_lon_source": "website",
            },
            "lat": response.css(
                ".Core-address > span > meta:nth-child(1)::attr(content)"
            ).get(),
            "lon": response.css(
                ".Core-address > span > meta:nth-child(2)::attr(content)"
            ).get(),
           
            "opening_hours": self.parse_opening_hours(
                response.css(".c-hours-details-wrapper::attr('data-days')").get()
            ),
            "phone": response.css(".Core-phone .Phone-link::text").getall(),
            "ref": f"{lat}-{lon}",
            "postcode": response.css(
                "#address > div:nth-child(5) > span.c-address-postal-code::text"
            ).get(),
            "name": f"{response.css(".LocationName-brand::text").get()} {response.css(".LocationName-geo::text").get()}",
            "state": None,
            "website": response.url,
        }


    def parse_opening_hours(self, text_data):
        self.logger.warning(f"Here is the {text_data}")

        data_days = json.loads(text_data)

        def format_time(time_int):
            """Formats a 24-hour time integer like 900 to 9:00, and 2100 to 21:00."""
            if isinstance(time_int, int) and time_int >= 0 and time_int <= 2359:
                hours = time_int // 100
                minutes = time_int % 100
                return f"{hours:02d}:{minutes:02d}"
            return None

        output = {
            "opening_hours": {
                weekday.get("day")[:3].capitalize(): f'{format_time(weekday.get("intervals")[0].get("start")) if weekday.get("intervals") else None} - {format_time(weekday.get("intervals")[0].get("end")) if weekday.get("intervals") else None}'
                for weekday in data_days
            }
        }

        return output
