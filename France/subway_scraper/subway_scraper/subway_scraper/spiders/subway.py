import scrapy
import re
import json
import datetime
import html


class SubwaySpider(scrapy.Spider):
    name = "subway"
    allowed_domains = ["subwayfrance.fr"]
    start_urls = ["https://subwayfrance.fr/restaurants"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        script_text = response.css("#__NEXT_DATA__").get()

        script_data = self.parse_script_data(script_text)

        for store in script_data.get("props").get("pageProps").get("data"):

            yield {
                "addr_full": store.get("address").get("street"),
                "brand": "Subway",
                "city": store.get("address").get("city"),
                "country": store.get("address").get("country"),
                "extras": {
                    "brand": "Subway",
                    "fascia": "Subway",
                    "category": "Restaurant",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "website",
                },
                "lat": store.get("geoPosition").get("lat"),
                "lon": store.get("geoPosition").get("lng"),
                "name": store.get("name"),
                "opening_hours": self.parse_opening_hours(
                    store.get("weeklyWorkingHours")
                ),
                "phone": store.get("phoneNumber"),
                "postcode": store.get("zip"),
                "ref": store.get("id"),
                "state": store.get("state"),
                "website": f'{response.url}/{store.get("name")}',
            }

    def parse_script_data(self, script_text):
        json_match = re.search(
            r'<script(?: id="__NEXT_DATA__")? type="application/(?:ld\+json|json)">(.*?)</script>',
            script_text,
            re.DOTALL,
        )
        if json_match:
            json_text = json_match.group(1).strip()

            json_text = html.unescape(json_text)
            data = re.sub(r"\s+", " ", json_text).strip()

            data = json.loads(data)

            return data

    def parse_opening_hours(self, store):

        full_days = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        short_days = ["Mon", "Tue", "Wed", "Thur", "Fri", "Sat", "Sun"]

        output = {"opening_hour": {}}

        for fday, sday in zip(full_days, short_days):
            interval = (
                store.get(fday, {}).get("intervals", [{}])[0]
                if store.get(fday, {}).get("intervals", [{}])
                else {}
            )
            output["opening_hour"][
                sday
            ] = f"{interval.get("startTime")}-{interval.get("endTime")}"

        return output
