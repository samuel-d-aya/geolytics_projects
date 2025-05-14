import json
import datetime
import scrapy


class JyskSpider(scrapy.Spider):
    name = "jysk"
    allowed_domains = ["jysk.gr"]
    start_urls = ["https://jysk.gr/stores-locator"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        data = json.loads(
            response.css(
                "div[data-jysk-react-component='StoresLocatorLayout']::attr(data-jysk-react-properties)"
            ).get()
        )

        stores = data.get("storesCoordinates")
        for store in stores:
            result = {
                "addr_full": f"{store.get("street")} {store.get("zipcode")} {store.get("city")}",
                "brand": "JYSK",
                "city": store.get("city"),
                "country": "Greece",
                "extras": {
                    "brand": "JYSK",
                    "fascia": "JYSK",
                    "category": "Retail",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.get("lat"),
                "lon": store.get("lng"),
                "name": f"JYSK {store.get('name')}",
                "opening_hours": self.parse_opening_hours(store.get("opening")),
                "phone": None,
                "postcode": store.get("zipcode"),
                "ref": store.get("id"),
                "state": None,
                "website": store.get("url"),
            }

            yield response.follow(
                url=f"{response.urljoin(store.get('url'))}",
                callback=self.parse_more_detail,
                meta={"result": result},
            )

    def parse_more_detail(self, response):

        result = response.meta.get("result")

        result["phone"] = response.css(
            "h2.customer-service__heading + div > a::text"
        ).get()

        yield result

    def parse_opening_hours(self, opening_hour):

        day_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        result = {}

        for entry in opening_hour:
            day_index = entry["day"] % 7
            day_name = day_map[day_index]

            if entry["all_day"]:
                result[day_name] = "00:00 - 24:00"
            else:
                start = f"{entry['starthours']:04d}"
                end = f"{entry['endhours']:04d}"
                formatted = f"{start[:2]}:{start[2:]} - {end[:2]}:{end[2:]}"
                result[day_name] = formatted

        return {"opening_hours": result}
