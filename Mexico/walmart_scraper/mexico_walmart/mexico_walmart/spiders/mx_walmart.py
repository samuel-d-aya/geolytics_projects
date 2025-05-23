import re
import json
import datetime
import scrapy


class MxWalmartSpider(scrapy.Spider):
    name = "mx_walmart"
    allowed_domains = [
        "lutprod.southcentralus.cloudapp.azure.com",
        "www.walmartmexico.com",
    ]
    start_urls = ["https://www.walmartmexico.com/conocenos/directorio-de-tiendas"]
    endpoint = "https://lutprod.southcentralus.cloudapp.azure.com/ajax/json/3b50d677d1843f52b340e44406c65aaf/"

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Origin": "https://www.walmartmexico.com",
        "Pragma": "no-cache",
        "Referer": "https://www.walmartmexico.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        states = response.css(".search-tool > option::attr(value)").getall()

        for state in states:

            api_endpoint = f"{self.endpoint}{state}"

            yield scrapy.Request(
                url=api_endpoint,
                headers=self.headers,
                callback=self.parse_stores,
            )

    def parse_stores(self, response):

        stores = json.loads(response.text)["data"]

        POSTCODE_RE = re.compile(r"^(CP\d{5})")

        for store in stores:
            m = POSTCODE_RE.match(store.get("col3"))
            postal_code = m.group(1) if m else ""

            yield {
                "addr_full": store.get("col3"),
                "city": store.get("col4"),
                "brand": "walmart",
                "country":"Mexico",
                 "extras": {
                    "brand": "walmart",
                    "fascia": store.get("col1"),
                    "category": "Food & Beverage",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Google",
                },
                "lat": None,
                "lon": None,
                "opening_hours": {"opening_hours":{}},
                "name": store.get("col2"),
                "phone": None,
                "ref": None,
                "postcode": postal_code.removeprefix("CP"),
                "state": store.get("primary"),
                "website": "https://www.walmartmexico.com/conocenos/directorio-de-tiendas"
            }
