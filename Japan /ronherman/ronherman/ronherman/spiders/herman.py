import datetime
import re
import scrapy


class HermanSpider(scrapy.Spider):
    name = "herman"
    allowed_domains = ["ronherman.jp"]
    start_urls = ["https://ronherman.jp/store"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        stores_element = response.css("body > div > div > div")
        lat_long_script_content = response.css("body > script:nth-child(15)").get()

        lat_lon_formated_list = re.findall(
            r'shopList\[(\d+)\]\["latitude"\]\s*=\s*"([\d.]+)";\s*shopList\[\1\]\["longitude"\]\s*=\s*"([\d.]+)";',
            lat_long_script_content,
        )

        lat_lon_data = {
            int(shop_id): {"latitude": lat, "longitude": lon}
            for shop_id, lat, lon in lat_lon_formated_list
        }

        for store in stores_element[1:]:

            store_area = store.css("span.store-detail__shop-area::text").get()
            store_name = store.css("span.store-detail__shop-name::text").get()

            store_info = store.css("div.store-detail__store-info::text").getall()
            clean_store_info = [
                line.strip("\n").strip("\t").strip("\r") for line in store_info
            ]
            ref = int(store.css("div::attr(id)").get().split("-")[-1])

            lat = lat_lon_data[ref]['latitude']
            lon = lat_lon_data[ref]['longitude']

            address = clean_store_info[0]
            postal_code = clean_store_info[1]

            phones_result = re.findall(r"\d{10,12}", " ".join(clean_store_info))
            phones = (
                phones_result
                if phones_result
                else store.css("div.store-detail__store-info > a::text").get()
            )
            hour_result = re.findall(
                r"(\d{1,2}[:：]\d{2}\s?[～-]\s?\d{1,2}[:：]\d{2})",
                " ".join(clean_store_info),
            )
            hours = (
                hour_result[0]
                if hour_result
                else [
                    line
                    for line in clean_store_info
                    if re.search("hours|days|week|day", line)
                ]
            )

            yield {
                "addr_full": address,
                "brand": "Ron Herman",
                "city": store_area,
                "country": "Japan",
                "extras": {
                    "brand": "Ron Herman",
                    "fascia": None,
                    "category": "Fashion",
                    "edit_date": datetime.datetime.now().strftime('%Y%m%d'),
                    "lat_lon_source": "Website",
                },
                "lat": lat,
                "lon": lon,
                "name": store_name,
                "opening_hours": {"opening_hours":self.parse_working_hours(hours)},
                "phone": phones,
                "postcode": postal_code,
                "ref": ref,
                "state": None,
                "website": "https://ronherman.jp/store",
            }

    def parse_working_hours(self, opening_hours):
        wk_hr = opening_hours[0] if isinstance(opening_hours, list) else opening_hours

        if re.match(r"^\d{1,2}[:：]\d{2}\s?[～-]\s?\d{1,2}[:：]\d{2}$", wk_hr):
            
            opening_hours = opening_hours.replace(' ～ ', '-')

            return {
                "Mon": opening_hours,
                "Tue": opening_hours,
                "Wed": opening_hours,
                "Thu": opening_hours,
                "Fri": opening_hours,
                "Sat": opening_hours,
                "Sun": opening_hours,
            }

        return {wk_hr}
