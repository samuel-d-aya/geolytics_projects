from urllib.parse import urlencode
import datetime
import json
import scrapy

class AbSpider(scrapy.Spider):
    name = "ab"
    allowed_domains = ["www.ab.gr"]
    start_urls = ["https://www.ab.gr/api/v1/"]

    cookies = {
        "dtCookie": "v_4_srv_4_sn_3815F2B3130DF48F43E189417FDE70F2_perc_100000_ol_0_mul_1_app-3A440a591b5a5302d3_1",
        # (other cookies omitted for brevity)
    }

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.7",
        "apollographql-client-name": "gr-ab-web-stores",
        "apollographql-client-version": "34022fea0f4ed59507c8e1fbc88bf897848cf8a4",
        # (other headers omitted for brevity)
    }

    params = {
        "operationName": "GetStoreSearch",
        "variables": '{"pageSize":9999,"lang":"gr","query":"","currentPage":0,"options":"STORELOCATOR_MINIFIED"}',
        "extensions": '{"persistedQuery":{"version":1,"sha256Hash":"9dc67fed7b358c14d80bbd04c6524ef76f4298a142ed7ab86732442271f4ad46"}}',
    }

    def start_requests(self):
        for url in self.start_urls:
            full_url = url + "?" + urlencode(self.params)
            yield scrapy.Request(
                url=full_url,
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse,  # type: ignore
            )

    def parse(self, response):  # type: ignore
        data = json.loads(response.text)  # type: ignore
        stores = data["data"]["storeSearchJSON"]["stores"]

        for store in stores:
            yield {
                "addr_full": store.get("address", {}).get("formattedAddress", ""),
                "brand": "AB Vassilopoulos",
                "city": store.get("address", {}).get("town", ""),
                "country": "Greece",
                "extras": {
                    "brand": "AB Vassilopoulos",
                    "fascia": store.get("groceryStoreType", ""),
                    "category": "Retail",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.get("geoPoint", {}).get("latitude", ""),
                "lon": store.get("geoPoint", {}).get("longitude", ""),
                "name": store.get("localizedName", ""),
                "opening_hours": self.parse_opening_hours(store.get("nextOpeningDay", {})),  # type: ignore
                "phone": store.get("address", {}).get("phone", ""),
                "postcode": store.get("address", {}).get("postalCode", ""),
                "ref": store.get("id", ""),
                "state": None,
                "website": store.get("urlName", ""),
            }

    def parse_opening_hours(self, opening_hour):  # type: ignore
        greek_days = [
            "Δευτέρα",  # Monday
            "Τρίτη",  # Tuesday
            "Τετάρτη",  # Wednesday
            "Πέμπτη",  # Thursday
            "Παρασκευή",  # Friday
            "Σάββατο",  # Saturday
            "Κυριακή",  # Sunday
        ]

        result = {
            "Mon": "04:00-19:00",
            "Tue": "04:00-19:00",
            "Wed": "04:00-19:00",
            "Thu": "04:00-19:00",
            "Fri": "04:00-19:00",
            "Sat": "04:00-19:00",
            "Sun": "05:30-14:00",
        }
        if opening_hour.get("weekDay") in greek_days:  # type: ignore
            result = {  # type: ignore
                day: f"{opening_hour.get("openingTime").split()[-1][:-3]}-{opening_hour.get("closingTime").split()[-1][:-3]}" for day in result if opening_hour.get("weekDay") != "Κυριακή"  # type: ignore
            }
        return {"opening_hours": result}
