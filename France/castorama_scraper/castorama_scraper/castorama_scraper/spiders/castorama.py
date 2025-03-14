import scrapy
import datetime


class CastoramaSpider(scrapy.Spider):
    name = "castorama"
    allowed_domains = ["www.castorama.fr"]
    start_urls = ["https://www.castorama.fr/magasin"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        store_list = response.css(
            '#main-content [data-test-id="page-layout-footer"]  [data-test-id="grid"] [data-test-id="link-list-container"]'
        )

        for store in store_list:

            store_region = store.css("a::text").get()
            detail_page_url = response.urljoin(store.css("a::attr(href)").get())
            yield response.follow(
                url=detail_page_url,
                meta={"region": store_region, "website": detail_page_url},
                callback=self.parse_detail_page,
            )

    def parse_detail_page(self, response):

        opening_hour_list = response.css(
            '#main-content [data-test-id="store-details-opening-times"] + div > div'
        )

        opening_hour = {
            op_hr.css('[data-test-id="store-day-name"]::text')
            .get(): op_hr.css('[data-test-id="store-opening-times"] > div::text')
            .get()
            for op_hr in opening_hour_list
        }
        print(
            f"we are currently {response.css(
                '#main-content [data-test-id="StoreBlockAddress"] p::text'
            )[1]
            .get()} and the region {response.meta.get("region")}"
        )
        yield {
            "addr_full": (
                response.css(
                    '#main-content [data-test-id="StoreBlockAddress"] p::text'
                )[-2].get()
                if response.css(
                    '#main-content [data-test-id="StoreBlockAddress"] p::text'
                )[0].get()
                else response.css(
                    '#main-content [data-test-id="StoreBlockAddress"] p::text'
                )[0].get()
                + +response.css(
                    '#main-content [data-test-id="StoreBlockAddress"] p::text'
                )[-2].get()
            ),
            "brand": "Castorama",
            "city": response.css(
                '#main-content [data-test-id="StoreBlockAddress"] p::text'
            )[-1]
            .get()
            .split(" - ")[1],
            "country": "France",
            "extras": {
                "brand": "Castorama",
                "fascia": response.css(
                    '#main-content [data-test-id="store-name-h1-text"]::text'
                ).get(),
                "category": "",
                "edit_date": datetime.datetime.now().strftime('%Y%m%d'),
                "lat_lon_source": "website",
            },
            "lat": response.css(
                '#main-content [data-test-id="StoreBlockAddress"] > a::attr(href)'
            )
            .get()
            .split("=")[1]
            .split(",")[0],
            "lon": response.css(
                '#main-content [data-test-id="StoreBlockAddress"] > a::attr(href)'
            )
            .get()
            .split("=")[1]
            .split(",")[1],
            "name": response.css(
                '#main-content [data-test-id="store-name-h1-text"]::text'
            ).get(),
            "opening_hours": {"opening_hours":self.parse_store_opening_hour(opening_hour)},
            "phone": response.css(
                '#main-content [data-test-id="StoreBlockPhone"] > a > span::text'
            ).get(),
            "postcode": response.css(
                '#main-content [data-test-id="StoreBlockAddress"] p::text'
            )[-1]
            .get()
            .split(" - ")[0],
            "ref": response.meta.get("website").split("/")[-1],
            "state": response.meta.get("region"),
            "website": response.meta.get("website"),
        }

    def parse_store_opening_hour(self, opening_data):

        return {
            day[:3]: hour.replace("h", ":") if hour else ""
            for day, hour in opening_data.items()
        }
