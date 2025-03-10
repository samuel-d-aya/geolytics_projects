import scrapy
import datetime
import re
import json


class BrocoSpider(scrapy.Spider):
    name = "broco"
    allowed_domains = ["www.bricodepot.fr"]
    start_urls = ["https://www.bricodepot.fr/catalogue/depot/"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        depot_list = response.css(
            ".bd-SearchDepot-Content > div:first-child > div > div > ul > li"
        )

        for depot in depot_list:
            depot_location = depot.css("div > div:first-child > h2::text").get()
            depot_detail_url = response.urljoin(
                depot.css("div > div:nth-child(2) > a::attr(href)").get()
            )

            yield response.follow(
                url=depot_detail_url,
                callback=self.parse_detail,
                meta={"store_loc": depot_location, "store_url": depot_detail_url},
            )

    def parse_detail(self, response):

        script_response = response.css("body > script:nth-child(36)").get()

        script_data = self.parse_scripts_data(script_response)

        store_address = response.css(
            ".bd-DepotCard address span:first-child::text"
        ).get()
        store_phone = response.css(
            ".bd-DepotCard div.bd-DepotLocation-Phone a span::text"
        ).get()
        store_hour_table = response.css(".bd-DepotCard table tr")

        store_opening_hour = {
            hour.css("td:nth-child(1)::text")
            .get(): hour.css("td:nth-child(2)::text")
            .get()
            for hour in store_hour_table
        }

        yield {
            "addr_full": store_address,
            "brand": "Brico Depot",
            "city": script_data.get("city"),
            "country": "France",
            "extras": {
                "brand": "Brico Depot",
                "fascia": "",
                "category": "",
                "edit_date": datetime.datetime.date,
                "lat_lon_source": "website",
            },
            "lat": script_data.get("latitude"),
            "lon": script_data.get("longitude"),
            "name": script_data.get("storeName"),
            "opening_hours": store_opening_hour,
            "phone": store_phone,
            "postcode": script_data.get("postalCode"),
            "ref": script_data.get("id"),
            "state": None,
            "website": response.meta.get("store_url"),
        }

    def parse_scripts_data(self, script_response):
        pattern = re.compile(
            r"var BricoMap = new SearchDepotMap\s*\(\s*\[(.*?)\]\s*,", re.DOTALL
        )

        match = pattern.search(script_response)
        if not match:
            return None

        store_data = match.group(1)

        result = {}

        kv_pattern = re.compile(
            r'(\w+):\s*(?:"([^"]*?)"|\'((?:[^\'\\]|\\.)*?)\'|([\d.]+))'
        )

        for match in kv_pattern.finditer(store_data):
            key = match.group(1)
            quoted_value_1 = match.group(2)
            quoted_value_2 = match.group(3)
            numeric_value = match.group(4)

            if numeric_value is not None:

                value = (
                    float(numeric_value) if "." in numeric_value else int(numeric_value)
                )
            else:

                value = quoted_value_1 if quoted_value_1 is not None else quoted_value_2

                value = value.replace("\\'", "'")

                # value = value.encode().decode('unicode_escape')

            result[key] = value

        return result
