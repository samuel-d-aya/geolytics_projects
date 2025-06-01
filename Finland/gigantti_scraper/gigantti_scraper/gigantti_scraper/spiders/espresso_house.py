import scrapy


class EspressoHouseSpider(scrapy.Spider):
    name = "espresso_house"
    allowed_domains = ["myespressohouse.com"]
    start_urls = ["https://myespressohouse.com/beproud/api/CoffeeShop/v2"]

    def parse(self, response):
        pass
