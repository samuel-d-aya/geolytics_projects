import re
import json
import html
import datetime
import scrapy


class ExkiSpider(scrapy.Spider):
    name = "exki"
    allowed_domains = ["www.exki.com"]
    start_urls = ["https://www.exki.com/fr/restaurants"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        script_text = response.xpath(
            '//*[@id="bh-sl-map-container"]/script/text()'
        ).get()
        store_list = self.parse_script_data(script_text)
        for store in store_list:
            if store.get("country", "") == "France":

                yield {
                    "addr_full": store.get("address"),
                    "brand": "Exki",
                    "city": store.get("city"),
                    "country": store.get("country"),
                    "extras": {
                        "brand": "Exki",
                        "fascia": store.get("restaurant"),
                        "category": "Food & Beverage",
                        "edit_date": str(datetime.datetime.now().date()),
                        "lat_lon_source": "website",
                    },
                    "lat": store.get("lat"),
                    "lon": store.get("lng"),
                    "name": store.get("name"),
                    "opening_hours": self.parse_opening_hours(store),
                    "phone": store.get("phone"),
                    "postcode": store.get("zip"),
                    "ref": store.get("id"),
                    "state": store.get("state"),
                    "website": f'https://www.exki.com/fr{store.get("menu_qr_code")}',
                }

    def parse_script_data(self, script_text):

        pattern = r"var select_store_locations\s*=\s*(\[.*?\]);"
        match = re.search(pattern, script_text, re.DOTALL)

        if not match:
            raise ValueError("No match for select_store_locations")

        json_data = match.group(1)

        json_data = re.sub(r",\s*([\]}])", r"\1", json_data)

        data = json.loads(json_data)
        return data

    def parse_opening_hours(self, store):

        return {
            "opening_hour": {
                "Mon": f'{store.get("monday_open")}{store.get("monday_close")}',
                "Tue": f'{store.get("tuesday_open")}{store.get("tuesday_close")}',
                "Wed": f'{store.get("wednesay_open")}{store.get("wednesday_close")}',
                "Thur": f'{store.get("thursday_open")}{store.get("thursday_close")}',
                "Fri": f'{store.get("friday_open")}{store.get("friday_close")}',
                "Sat": f'{store.get("saturday_open")}{store.get("saturday_close")}',
                "Sun": f'{store.get("sunday_open")}{store.get("sunday_close")}',
            }
        }
