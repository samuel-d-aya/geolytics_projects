import scrapy
import datetime


class OtacosSpider(scrapy.Spider):
    name = "otacos"
    allowed_domains = ["o-tacos.com"]
    start_urls = ["https://o-tacos.com/nos-restos"]

    def start_requests(self):
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://o-tacos.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "X-Hermes-Locale": "us_en",
            "Accept-Language": "en-US,en;q=0.6",
            "Origin": "https://o-tacos.com/",
            "Sec-Ch-Ua": '"Chromium";v="134", "Not=A?Brand";v="24", "Brave";v="134"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Sec-Gpc": "1",
        }
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, headers=headers, meta={"dont_merge_cookies": True}
            )

    def parse(self, response):

        store_list = response.css("div.maptacos-content-listing-restos > div")

        for store in store_list:

            yield {
                "addr_full": store.css("p:nth-child(2)::text").get(),
                "brand": "Otacos",
                "city": store.css("p:nth-child(3)::text").get().split()[1],
                "country": "France",
                "extras": {
                    "brand": "otacos",
                    "fascia": "otacos",
                    "category": "Food & Beverages",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "website",
                },
                "lat": store.attrib.get("data-lat"),
                "lon": store.attrib.get("data-lng"),
                "name": store.css("p:nth-child(1)::text").get(),
                "opening_hours": self.parse_opening_hours(store),
                "phone": None,
                "postcode": store.css("p:nth-child(3)::text").get().split()[0],
                "ref": store.attrib.get("data-lat") + "-" + store.attrib.get("data-lng"),
                "state": None,
                "website": "https://o-tacos.com/nos-restos",
            }

    def parse_opening_hours(self, store):

        weeklyhour = store.css("p::text")

        output = {
            "opening_hours": {
                weekday.get()
                .split(":", 1)[0][:3]: weekday.get()[weekday.get().find(":") + 2 :]
                .replace("h", ":")
                for weekday in weeklyhour[3:]
            }
        }

        return output
