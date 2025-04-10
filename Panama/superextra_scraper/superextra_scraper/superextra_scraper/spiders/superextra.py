import scrapy
from scrapy_playwright.page import PageMethod


class SuperXtraSpider(scrapy.Spider):
    name = "superxtra"
    start_urls = ["https://www.superxtra.com/sucursales"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "div.product-item", timeout=15000),
                    ],
                    "playwright_page_goto_kwargs": {
                        "timeout": 60000,
                        "wait_until": "domcontentloaded",
                    },
                },
                callback=self.parse,
            )

    def parse(self, response):
        for branch in response.css("div.product-item"):
            name = branch.css("div.text-primary::text").get(default="").strip()
            address = branch.css("div.text-center.p-4 p:nth-of-type(1)::text").get(default="").strip()
            hours = branch.css("div.text-center.p-4 p:nth-of-type(2)::text").get(default="").strip()
            location_url = branch.css("a::attr(href)").get(default="")

            yield {
                "name": name,
                "address": address,
                "hours": hours,
                "location_url": location_url,
            }
