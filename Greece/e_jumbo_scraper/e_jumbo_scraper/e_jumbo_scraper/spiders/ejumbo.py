import re
import datetime
import requests
import scrapy


class EjumboSpider(scrapy.Spider):
    name = "ejumbo"
    allowed_domains = ["corporate.e-jumbo.gr"]
    start_urls = ["https://corporate.e-jumbo.gr/en/stores-premises/"]

    cookies = {
        "ASP.NET_SessionId": "fherxpkx3jxndsm1ecd5hzmm",
        "VisitorGUID": "707a2a63-8cfd-4f47-9ff9-e8f9c3af12b6",
        "PreviousCountryCode": "GR",
        "CookiesConsents": "{%22P%22:true%2C%22CC%22:{%223%22:true%2C%224%22:true}}",
        "VisitorState": "siteId=1&countryCode=gr&languageCode=el&currencyCode=eur",
    }

    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-US,en;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json; charset=UTF-8",
        "origin": "https://corporate.e-jumbo.gr",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://corporate.e-jumbo.gr/en/stores-premises/",
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    json_data = {
        "id": 124432,
        "path": -2047353799,
        "languageId": 2,
        "country": "GR",
        "city": "",
        "department": "",
        "area": "",
        "type": 0, 
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        js_response = requests.post(
            "https://corporate.e-jumbo.gr/services/secure/StoresService.svc/GetStores",
            cookies=self.cookies,
            headers=self.headers,
            json=self.json_data,
            timeout=60,
        )

        json_data = js_response.json().get("d", {}).get("Items", [])

        for store_list in json_data:
            for store in store_list:
                lat = store.get("Latitude")
                lon = store.get("Longitude")
                city_state = self.reverse_geocode_osm(lat, lon)

                yield {
                    "addr_full": store.get("AddressLine1"),
                    "brand": "Jumbo",
                    "city": store.get("Area"),
                    "country": city_state.get("country"),
                    "extras": {
                        "brand": "Jumbo",
                        "fascia": "Jumbo",
                        "category": "Retail",
                        "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                        "lat_lon_source": "Third Party",
                    },
                    "lat": lat,
                    "lon": lon,
                    "name": store.get('Name'),
                    "opening_hours": self.parse_opening_hours(store.get("WorkingHours", "")),
                    "phone": store.get("Phone"),
                    "postcode": store.get("PostalCode"),
                    "ref": f"{lat},{lon}",
                    "state": city_state.get("state"),
                    "website": response.url,
                }

    def reverse_geocode_osm(self, lat, lon):
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json", "addressdetails": 1}
        headers = {"User-Agent": "ejumbo (ejumbo@email.com)"}

        response = requests.get(url, params=params, headers=headers)
        data = response.json()

        address = data.get("address", {})
        return {
            "city": address.get("city") or address.get("town") or address.get("village"),
            "state": address.get("county"),
            "country": address.get("country"),
            "postcode": address.get("postcode"),
        }

    def parse_opening_hours(self, opening_hour):
        day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        full_to_abbr = {
            "Monday": "Mon",
            "Tuesday": "Tue",
            "Wednesday": "Wed",
            "Thursday": "Thu",
            "Friday": "Fri",
            "Saturday": "Sat",
            "Sunday": "Sun",
        }

        text = opening_hour.replace("\xa0", " ")  # clean non-breaking spaces
        hours = {day: "00:00-00:00" for day in day_order}

        for match in re.finditer(
            r"(\w+)(?:-(\w+))?\s+(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})", text
        ):
            start_day, end_day, open_time, close_time = match.groups()
            if end_day:
                start_idx = day_order.index(full_to_abbr[start_day])
                end_idx = day_order.index(full_to_abbr[end_day])
                for i in range(start_idx, end_idx + 1):
                    hours[day_order[i]] = f"{open_time}-{close_time}"
            else:
                abbr = full_to_abbr.get(start_day)
                if abbr:
                    hours[abbr] = f"{open_time}-{close_time}"

        return {"opening_hours": hours}
