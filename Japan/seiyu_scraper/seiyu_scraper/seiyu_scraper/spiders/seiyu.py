import datetime
import re
import scrapy


class SeiyuSpider(scrapy.Spider):
    name = "seiyu"
    allowed_domains = ["www.seiyu.co.jp"]
    start_urls = ["https://www.seiyu.co.jp/searchshop/"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_city_url)

    def parse_city_url(self, response):
        city_links = response.css(
            ".shop_search_map_prefrecture_link::attr(href)"
        ).getall()

        for city_link in city_links:
            yield response.follow(
                url=response.urljoin(city_link), callback=self.parse_store_url
            )

    def parse_store_url(self, response):
        store_links = response.css(".shop_search_individual_link::attr(href)").getall()
        city_name = response.css(".shop_search_query_prefrecture_link::text").get()
        state_name = response.css("li.shop_search_query_item.o-current a::text").get()

        for store_link in store_links:
            yield response.follow(
                url=store_link,
                meta={"city": city_name, "state": state_name},
                callback=self.parse_store_details,
            )

    def parse_store_details(self, response):

        store = response.css(".shop_information_list")
        location = response.css(".shop_information_map::attr(data-ll)").get()
        address = (
            store.css(".shop_detail > dl:nth-child(2) > dd::text").get()
            or store.css("li:nth-child(4) > dl > dd::text").get()
        )

        opening_hours = response.css(".shop_detail > dl:nth-child(1) > dd::text").get()

        print(f"\n\n{address}\n\n")

        yield {
            "addr_full": address,
            "brand": "Ito-Yokado",
            "city": response.meta["city"],
            "country": "Japan",
            "extras": {
                "brand": "Ito-Yokado",
                "fascia": "Ito-Yokado",
                "category": "Food and Beverage",
                "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                "lat_lon_source": "Google",
            },
            "lat": location.split(",")[0],
            "lon": location.split(",")[1],
            "name": response.css(".shop_heading_title_text::text").get(),
            "opening_hours": {"opening_hours":self.parse_opening_hours(opening_hours)},
            "phone": store.css("li:nth-child(3) > dl > dd > a::text").get(),
            "postcode": address.split()[0] if address else None,
            "ref": f"{location.split(",")[0]}-{location.split(",")[1]}",
            "state": response.meta["state"],
            "website": response.url,
        }

    def parse_opening_hours(self, opening_hours):

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        result = {}

        # Normalize the input
        text = opening_hours.replace("\\u3000", " ").replace("　", " ").strip()

        # Check for 24-hour open phrases
        if "年中無休" in text and "24" in text:
            return {day: "00:00-24:00" for day in days}
        if "24時間" in text:
            return {day: "00:00-24:00" for day in days}
        if "all year" in text.lower() or "open year" in text.lower():
            return {day: "00:00-24:00" for day in days}

        # Match time range
        match = re.search(
            r"(\d{1,2}):?(\d{0,2})\s*[–~〜～\-]\s*(\d{1,2}):?(\d{0,2})", text
        )
        if match:
            h1, m1 = match.group(1), match.group(2) or "00"
            h2, m2 = match.group(3), match.group(4) or "00"
            start = f"{int(h1):02}:{int(m1):02}"
            end = f"{int(h2):02}:{int(m2):02}"
            return {day: f"{start}-{end}" for day in days}

        # Default fallback
        return {day: "00:00-24:00" for day in days}
