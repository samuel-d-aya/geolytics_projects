import scrapy
import datetime
from urllib.parse import urlparse, parse_qs
from datetime import datetime as dt

class FarmaciaSpider(scrapy.Spider):
    name = "farmacias"
    start_urls = ['https://www.farmaciasannicolas.com/sucursales']

    def parse(self, response):
        # Step 1: Get all the city summary <p> elements (order matters!)
        city_elements = response.css('#branch-offices-list > div > a > div.text > p::text').getall()
        
        name_element = response.css('#branch-offices-list > div > a > div.text > div > strong::text').getall()

        # Step 2: Get all the detailed branch divs with ID starting with SC
        branch_elements = response.css('div[id^="SC"]')

        # Step 3: Zip both lists together (they must be in same order)
        for city, name, branch in zip(city_elements, name_element, branch_elements):
            branch_id = branch.attrib.get('id')

            # Address
            address = branch.css('div.row.gx-0 div.col-xl > p::text').get()
            address = address.strip() if address else None

            # Opening hours
            raw_hours = branch.css('div.row.gx-0 div.col > p::text').getall()
            opening_hours = self.parse_hours(raw_hours)

            # Href with lat/lon
            href = branch.css('div.actions a::attr(href)').get()
            lat = lon = None
            if href:
                parsed_url = urlparse(href)
                query_params = parse_qs(parsed_url.query)
                latlon = query_params.get('ll', [None])[0]
                if latlon:
                    lat, lon = latlon.split(',')

            yield {
                
                "addr_full": address,
                "city": city.strip(),
                "country": "El Salvador",
                "brand": "Farmacias San Nicolás",
                "extras": {
                    "brand": "Farmacias San Nicolás",
                    "fascia": "Farmacias San Nicolás",
                    "category": "Pharmacy",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": 'google',
                },
                "lat": lat,
                "lon": lon,
                "opening_hours": {"opening_hours":opening_hours},
                "phone": None,
                "ref": branch_id,
                "postcode": None,
                "name": f"{"Farmacias San Nicolás"} {name.strip() if city else None}",
                "state": None,
                "website": response.url
            }

    def parse_hours(self, hours_list):
        days_map = {
            "Lunes": "Mon",
            "Martes": "Tue",
            "Miércoles": "Wed",
            "Jueves": "Thu",
            "Viernes": "Fri",
            "Sábado": "Sat",
            "Domingo": "Sun"
        }
        
        def clean_time(time_str):
            return (
                time_str.lower()
                .replace("a. m.", "AM")
                .replace("p. m.", "PM")
                .replace("a.m.", "AM")
                .replace("p.m.", "PM")
                .replace("a. m.", "AM")  # Weird Unicode spacing
                .replace("p. m.", "PM")
                .replace(" ", "")
                .strip()
            )

        opening_hours = {}

        for line in hours_list:
            try:
                day_part, time_part = line.split(": ", 1)
                day_abbr = days_map.get(day_part.strip())
                if not day_abbr or " - " not in time_part:
                    continue

                open_time, close_time = time_part.split(" - ")
                open_24 = dt.strptime(clean_time(open_time), "%I:%M%p").strftime("%H:%M")
                close_24 = dt.strptime(clean_time(close_time), "%I:%M%p").strftime("%H:%M")

                opening_hours[day_abbr] = f"{open_24}-{close_24}"
            except Exception as e:
                self.logger.warning(f"Failed to parse line '{line}': {e}")
                continue

        return opening_hours

