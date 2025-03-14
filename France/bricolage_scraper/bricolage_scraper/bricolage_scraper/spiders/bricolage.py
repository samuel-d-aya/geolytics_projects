import re
import json
import html
import datetime
import scrapy

PAGENUMBER = 17


class BricolageSpider(scrapy.Spider):
    name = "bricolage"
    allowed_domains = ["magasin.mr-bricolage.fr"]
    start_urls = ["https://magasin.mr-bricolage.fr/"]

    def start_requests(self):
        for page in range(1, PAGENUMBER + 1):
            url = f"{self.start_urls[0]}search?country=FR&page={page}"
            self.logger.warning(f"Currently on Page {page}")
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        relative_urls = response.css(
            ".lf-results-list__results ul > li [data-lf-infos]::attr(href)"
        ).getall()

        self.logger.warning(f"The stores on this page {len(relative_urls)}")

        for url in relative_urls:
            absolute_url = response.urljoin(url)

            yield response.follow(
                url=absolute_url,
                meta={"url": absolute_url},
                callback=self.parse_detail_page,
            )

    def parse_detail_page(self, response):

        script_text = response.css("#lf-body > script:nth-child(4)").get()
        store = self.parse_script_data(script_text)

        yield {
            "addr_full": store.get("address").get("streetAddress"),
            "brand": "Mr Bricolage",
            "city": store.get("address").get("addressLocality"),
            "country": store.get("address").get("addressCountry"),
            "extras": {
                "brand": "Mr Bricolage",
                "fascia": "Mr Bricolage",
                "category": "Retail",
                "edit_date": str(datetime.datetime.now().date()),
                "lat_lon_source": "website",
            },
            "lat": store.get("geo").get("latitude"),
            "lon": store.get("geo").get("longitude"),
            "name": store.get("name"),
            "opening_hours": self.parse_opening_hours(store.get("openingHours")),
            "phone": store.get("telephone"),
            "postcode": store.get("address").get("postalCode"),
            "ref": store.get("url").split("-")[0].replace("/", ""),
            "state": None,
            "website": response.meta.get("url"),
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

    def parse_opening_hours(self, opening_hours):

        hours_list = re.split(r",\s*", opening_hours.strip())

        schedule = {}

        pattern = re.compile(r"([A-Za-z]{2})\s(\d{2}:\d{2})\s-\s(\d{2}:\d{2})")

        day_mapping = {
            "Mo": "Mon",
            "Tu": "Tue",
            "We": "Wed",
            "Th": "Thu",
            "Fr": "Fri",
            "Sa": "Sat",
            "Su": "Sun",
        }

        for entry in hours_list:
            match = pattern.match(entry)
            if match:
                day, open_time, close_time = match.groups()
                full_day = day_mapping.get(day, day)

                if full_day in schedule:
                    schedule[full_day] += f"  &  {open_time} - {close_time}"
                else:
                    schedule[full_day] = f"{open_time} - {close_time}"

        return {"opening_hours": schedule}
