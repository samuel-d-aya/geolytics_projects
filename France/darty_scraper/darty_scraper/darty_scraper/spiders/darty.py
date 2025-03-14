import scrapy
import re
import html
import json
import datetime


class DartySpider(scrapy.Spider):
    name = "darty"
    allowed_domains = ["magasin.darty.com"]
    start_urls = ["https://magasin.darty.com/fr"]

    def start_requests(self):
        for page in range(1, 11):
            yield scrapy.Request(
                url=f"{self.start_urls[0]}?page={page}", callback=self.parse
            )

    def parse(self, response):

        store_list = response.css("[data-lf-location] > script")

        for script in store_list:

            store = self.parse_script_data(script.get())

            yield {
                "addr_full": store.get("address").get("streetAddress"),
                "brand": "Darty",
                "city": store.get("address").get("addressLocality"),
                "country": store.get("address").get("addressCountry"),
                "extras": {
                    "brand": "Darty",
                    "fascia": "Darty",
                    "category": "Retail",
                    "edit_date": datetime.datetime.now().strftime('%Y%m%d'),
                    "lat_lon_source": "website",
                },
                "lat": store.get("geo", {}).get("latitude"),
                "lon": store.get("geo", {}).get("longitude"),
                "name": store.get("name"),
                "opening_hours": self.parse_opening_hours(store.get("openingHours")),
                "phone": store.get("telephone"),
                "postcode": store.get("address").get("postalCode"),
                "ref": store.get("url").split("-")[0].replace("/", ""),
                "state": None,
                "website": response.urljoin(store.get("url")),
            }

    def parse_script_data(self, script_text):
        json_match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>',
            script_text,
            re.DOTALL,
        )
        if json_match:
            json_text = json_match.group(1).strip()

            json_text = html.unescape(json_text)
            data = re.sub(r"\s+", " ", json_text).strip()

            data = json.loads(data)

            return data

    def parse_opening_hours(self, hours_string):
        days_map = {
            "Mo": "Mon",
            "Tu": "Tue",
            "We": "Wed",
            "Th": "Thu",
            "Fr": "Fri",
            "Sa": "Sat",
            "Su": "Sun",
        }

        hours_dict = {}
        entries = re.findall(r"(\b[A-Za-z]{2})\s([\d:]+ - [\d:]+)", hours_string)

        for day, time in entries:
            full_day = days_map.get(day, day)
            if full_day in hours_dict:
                hours_dict[full_day] += f", {time}"
            else:
                hours_dict[full_day] = time

        return {"opening_hours": hours_dict}
