import re
import datetime
import scrapy
from scrapy_playwright.page import PageMethod


class GoodysSpider(scrapy.Spider):
    name = "goodys"
    allowed_domains = ["www.goodys.com"]
    start_urls = ["https://www.goodys.com/en/katastimata/"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                    ],
                },
                callback=self.parse,
            )

    async def parse(self, response):

        page = response.meta.get("playwright_page")

        stores = await page.query_selector_all(".store")

        # stores = response.css(".store")

        for nth_child in range(1, len(stores) + 1):

            show_btn = await page.query_selector(
                f".store:nth-child({nth_child}) .storeRowBtm"
            )
            await show_btn.click()

            full_page_html = await page.content()
            new_response = response.replace(body=full_page_html, encoding="utf-8")
            store = new_response.css(f".store:nth-child({nth_child})")

            google_link = store.css("#google_directions-link::attr(href)").get()

            city = (
                store.css(".name .address::text").get().split(",")[-1].split()
                if len(store.css(".name .address::text").get().split(",")) == 2
                else None
            )

            self.logger.info(
                f"\n\n{store.css(".name .address::text").get().split(",")}\n\n"
            )

            yield {
                "addr_full": store.css(".name .address::text").get(),
                "brand": "Goody's",
                "city": self.parse_city(
                    store.css(".name .address::text").get().split(",")
                ),
                "country": "Greece",
                "extras": {
                    "brand": "Goody's Burger House",
                    "fascia": "Goody's Burger House",
                    "category": "Food and Beverage",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Website",
                },
                "lat": google_link.split("/")[-1].split(",")[0],
                "lon": google_link.split("/")[-1].split(",")[-1],
                "name": f"Goody's {store.css(".name .region::text").get()}",
                "opening_hours": self.parse_opening_hours(
                    store.css(".workinghours li")
                ),
                "phone": store.css(".name .phone > a::text").get(),
                "postcode": self.parse_postcode(
                    store.css(".name .address::text").get().split(",")
                ),
                "ref": store.css(".store_info::attr(data-storeid)").get(),
                "state": None,
                "website": response.url,
            }

    def parse_opening_hours(self, opening_hours):

        op_hr = {}

        # days_mapping = {
        #     "Δευτέρα": "Mon",
        #     "Τρίτη": "Tue",
        #     "Τετάρτη": "Wed",
        #     "Πέμπτη": "Thu",
        #     "Παρασκευή": "Fri",
        #     "Σάββατο": "Sat",
        #     "Κυριακή": "Sun",
        # }

        days_mapping = {
            "Monday": "Mon",
            "Tuesday": "Tue",
            "Wednesday": "Wed",
            "Whursday": "Thur",
            "Friday": "Fri",
            "Saturday": "Sat",
            "Sunday": "Sun",
        }

        for working_hour in opening_hours:

            # self.logger.info(
            #     f"\n\n{working_hour.css(".day::text").get()} {re.sub(r'\s+', '',working_hour.css(".hour_range > span::text").get())} \n\n"
            # )
            op_hr[days_mapping.get(working_hour.css(".day::text").get())] = re.sub(
                r"\s+", "", working_hour.css(".hour_range > span::text").get()
            )

        return {"opening_hours": op_hr}

    def parse_city(self, addr_list):

        if len(addr_list) == 2:

            cp = addr_list[-1].split()
            if len(cp) == 3:
                return cp[0]
            if len(cp) > 3:
                return " ".join(cp[:2])
            return cp[-1]

        if len(addr_list) > 3:
            return addr_list[-2]

        return None

    def parse_postcode(self, addr_list):

        if len(addr_list) == 2:

            cp = addr_list[-1].split()
            if len(cp) > 3:
                return "".join(cp[-2:])

        if len(addr_list) > 3:
            return addr_list[-1]

        return None
