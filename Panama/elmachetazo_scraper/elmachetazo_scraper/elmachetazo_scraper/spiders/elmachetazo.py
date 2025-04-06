import scrapy
import json
import datetime
import re


class ElmachetazoSpider(scrapy.Spider):
    name = "elmachetazo"
    allowed_domains = ["www.elmachetazo.com"]
    start_urls = ["https://www.elmachetazo.com/mapa-tiendas"]

    def parse(self, response):
        # Try to extract the script content from the page
        script_content = response.xpath('/html/body/script[3]/text()').get()

        if script_content:
            # Find the content after __RUNTIME__ and before __STATE__
            try:
                # Locate the start and end of the JSON data
                start_index = script_content.find('__RUNTIME__ = ') + len('__RUNTIME__ = ')
                end_index = script_content.find('__STATE__ = {')
                
                if start_index == -1 or end_index == -1:
                    self.logger.error("Could not find the JSON data properly in the script content.")
                    return

                # Extract the JSON part from the script content
                json_data_str = script_content[start_index:end_index].strip().rstrip(';')

                # Load the JSON data
                data = json.loads(json_data_str)

                # Extract store information
                store_descriptions = data["extensions"]["store.custom#mapa-tienda\u002Fstore-in-map"]["content"]["descriptions"]
                
                for store in store_descriptions:
                    address = store.get("direction", "")
                    city = "Panama"  # We can assume the city is Panama for all stores in the current case
                    lat = store.get("latitud")
                    lon = store.get("longitud")
                    ref = f"{lat}-{lon}"  # Create a reference based on lat/lon

                    # Extract opening hours and convert to proper structure
                    opening_hours = self.parse_opening_hours(store)

                    yield {
                        "addr_full": address,
                        "brand": "Elmachetazo",
                        "city": city,
                        "country": "Panama",
                        "extras": {
                            "brand": "Elmachetazo",
                            "fascia": "Elmachetazo",
                            "category": "Filling Station",
                            "edit_date": str(datetime.datetime.now().date()),
                            "lat_lon_source": "Extracted from site"
                        },
                        "lat": lat,
                        "lon": lon,
                        "name": store.get("title", ""),
                        "opening_hours": opening_hours,
                        "phone": None,
                        "postcode": None,
                        "ref": ref,
                        "state": None,
                        "website": "https://www.elmachetazo.com/mapa-tiendas"
                    }

            except (IndexError, ValueError) as e:
                self.logger.error(f"Error extracting or parsing JSON data: {e}")
        else:
            self.logger.error("No script content found at the specified XPath.")

    def parse_opening_hours(self, store):
        """ Parse and convert opening hours for each store """
        opening_hours = {}

        # Extract and process "horary" (Monday-Saturday) and "horary2" (Sunday)
        horary = store.get("horary", "").strip()
        horary2 = store.get("horary2", "").strip()

        if horary:  # If 'horary' exists, it applies to Mon-Sat
            opening_hours.update(self.convert_to_24h(horary, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]))
        else:  # If 'horary' is empty, set Mon-Sat to "Closed"
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
                opening_hours[day] = "Closed"
        
        if horary2:  # If 'horary2' exists, it applies to Sunday
            opening_hours["Sun"] = self.convert_to_24h(horary2)
        else:  # If 'horary2' is empty, set Sunday to "Closed"
            opening_hours["Sun"] = "Closed"

        return opening_hours

    def convert_to_24h(self, time_str, days=None):
        """Convert opening/closing hours string to 24-hour format and map to days"""
        if not isinstance(time_str, str) or not time_str:
            self.logger.warning(f"Invalid or empty time string: {time_str}. Returning 'Closed'.")
            return "Closed"

        time_str = time_str.strip().lower()

        # Match the pattern for hours (e.g., '6:00am - 9:00pm')
        match = re.match(r"(.*?)(\d{1,2}:\d{2}\s*(am|pm))\s*-\s*(\d{1,2}:\d{2}\s*(am|pm))", time_str)
        if match:
            open_time, close_time = match.group(2), match.group(4)
            open_time = self.convert_to_24h_format(open_time)
            close_time = self.convert_to_24h_format(close_time)

            if days:
                # If specific days are given, assign the times to those days
                hours = {day: f"{open_time}-{close_time}" for day in days}
                return hours
            return f"{open_time}-{close_time}"

        self.logger.warning(f"Time string did not match expected format: {time_str}")
        return "Closed"  # In case the format doesn't match the expected time

    def convert_to_24h_format(self, time_str):
        """Convert '6:00 am' format to 24-hour '06:00'."""
        match = re.match(r"(\d{1,2}):?(\d{0,2})?\s*(am|pm)", time_str, re.IGNORECASE)
        if match:
            hour, minute, period = match.groups()
            hour = int(hour)
            minute = minute if minute else "00"

            if period.lower() == "pm" and hour != 12:
                hour += 12
            elif period.lower() == "am" and hour == 12:
                hour = 0

            return f"{hour:02}:{minute}"

        self.logger.warning(f"Failed to convert time: {time_str}")
        return time_str  # If conversion fails, return the original time string
