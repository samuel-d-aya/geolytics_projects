import scrapy
import json
import datetime

class BacOfficesSpider(scrapy.Spider):
    name = "bac"
    allowed_domains = ["baccredomatic.com"]
    start_urls = ["https://www.baccredomatic.com/graphql"]

    cities = [
        {"city": "San Salvador", "lat": 13.6929403, "lng": -89.2181911}
    ]

    def start_requests(self):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        for city_info in self.cities:
            city = city_info["city"]
            lat = city_info["lat"]
            lng = city_info["lng"]
            proximity = f"{lat},{lng}<500km"

            payload = {
                "operationName": "officeBranches",
                "query": """query officeBranches($langcode: String!, $tids: String!, $field_coordinates_proximity: String!) {
                    officeBranchesQuery(contextualFilter: {langcode: $langcode, tid: $tids, field_coordinates_proximity: $field_coordinates_proximity}) {
                        results {
                            ... on NodeOfficeBranch {
                                entityId
                                entityLabel
                                fieldAddress
                                fieldCoordinates { lat lng }
                                fieldEmail
                                fieldMobilePhone
                                fieldOfficeBranchType { entity { entityLabel } }
                                fieldSchedule { day starthours endhours }
                            }
                        }
                    }
                }""",
                "variables": {
                    "langcode": "es-sv",
                    "tids": "",
                    "field_coordinates_proximity": proximity
                }
            }

            yield scrapy.Request(
                url=self.start_urls[0],
                method="POST",
                headers=headers,
                body=json.dumps(payload),
                callback=self.parse_response,
                meta={"searched_city": city, "searched_coordinates": proximity}
            )

    def parse_response(self, response):
        data = response.json()
        offices = data.get("data", {}).get("officeBranchesQuery", {}).get("results", [])
        searched_city = response.meta["searched_city"]
        searched_coordinates = response.meta["searched_coordinates"]

        day_map = {
            0: "Sun",
            1: "Mon",
            2: "Tue",
            3: "Wed",
            4: "Thu",
            5: "Fri",
            6: "Sat",
        }

        for office in offices:
            # Format mobile phone safely
            field_mobile_phone = office.get("fieldMobilePhone")
            if isinstance(field_mobile_phone, list) and field_mobile_phone:
                phone = field_mobile_phone[0]
            else:
                phone = None

            # Build opening_hours
            opening_hours = {}
            for schedule in office.get("fieldSchedule", []):
                day_num = schedule.get("day")
                start = schedule.get("starthours")
                end = schedule.get("endhours")

                if day_num is not None and start is not None and end is not None:
                    start_str = f"{start:04d}"
                    end_str = f"{end:04d}"
                    start_formatted = f"{start_str[:2]}:{start_str[2:]}"
                    end_formatted = f"{end_str[:2]}:{end_str[2:]}"
                    day_name = day_map.get(day_num)
                    if day_name:
                        opening_hours[day_name] = f"{start_formatted}-{end_formatted}"
                        
            # Add default Monday hours if not present
            if "Mon" not in opening_hours:
                opening_hours["Sun"] = "09:00-16:00"

            yield {
                "addr_full": office.get("fieldAddress"),
                "city": searched_city,
                "country": "El Salvador",
                "brand": "BAC Credomatic",
                "extras": {
                    "brand": "BAC Credomatic",
                    "fascia": office.get("fieldOfficeBranchType", {}).get("entity", {}).get("entityLabel"),
                    "category": "Other",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": 'Third Party'
                },
                "lat": office.get("fieldCoordinates", {}).get("lat"),
                "lon": office.get("fieldCoordinates", {}).get("lng"),
                "opening_hours": {"opening_hours": opening_hours},
                "phone": phone,
                "ref": office.get("entityId"),
                "postcode": None,
                "name": office.get("entityLabel"),
                "state": None,
                "website": "https://www.baccredomatic.com/es-sv/ubicaciones"
            }
