import scrapy
import json
import re
import html
import datetime

class NoveyStockSpider(scrapy.Spider):
    name = 'novey'
    start_urls = ['https://www.novey.com.pa/rest/V1/branchoffices/stock']

    def start_requests(self):
        # Define the payload data
        payload = {
            "stockId": "6",
            "sku": None
        }

        # Convert the payload to JSON format
        body = json.dumps(payload)

        # Set the headers (Content-Type as application/json)
        headers = {
            'Content-Type': 'application/json',
        }

        # Send the POST request with the payload and headers
        yield scrapy.Request(
            url=self.start_urls[0],
            method='POST',
            body=body,
            headers=headers,
            callback=self.parse_response
        )

    def parse_response(self, response):
        # Log the raw response text to inspect the structure
        self.logger.info(f"Response Text: {response.text}")

        # Check if the response contains the expected message
        try:
            # Extract the message content from the response body
            message = response.xpath('//response/message').get()

            if not message:
                self.logger.error("No 'message' element found in the response.")
                return  # Early return to prevent further errors

            # Extract the individual items from the message
            items = response.xpath('//response/message/item/text()').getall()

            if not items:
                self.logger.error("No items found in the message.")
                return

            for item in items:
                try:
                    # Each 'item' is a JSON string, so we parse it
                    branch_info = json.loads(item)

                    # Extract and process the 'frontend_description' field
                    frontend_description = branch_info.get('frontend_description', "")

                    # Call the function to extract opening hours
                    opening_hours = self.extract_opening_hours(frontend_description)

                    # Yield the relevant data
                    yield {
                        'addr_full': branch_info.get('street'),
                        'city': branch_info.get('city'),
                        'country': 'Panama',
                        'brand': 'Novey',
                        'extras': {
                            'brand': 'Novey',
                            'fascia': 'Novey',
                            'category': 'Hardware Store',
                            'edit_date': datetime.datetime.now().strftime("%Y%m%d"),
                            'lat_lon_source': 'website',
                        },
                        'lat': branch_info.get('latitude'),
                        'lon': branch_info.get('longitude'),
                        'opening_hours': opening_hours,
                        'phone': branch_info.get('phone'),
                        'ref': branch_info.get('source_code'),
                        'postcode': branch_info.get('postcode'),
                        'name': branch_info.get('name'),
                        'state': branch_info.get('region'),
                        'website': "https://www.novey.com.pa/sucursales-y-horarios",
                    }

                except json.JSONDecodeError:
                    self.logger.error(f"Failed to decode branch info: {item}")
        except Exception as e:
            self.logger.error(f"Failed to parse response: {e}")

    def extract_opening_hours(self, frontend_description):
        # If no description is available, return an empty dictionary
        if not frontend_description or frontend_description.lower() == 'null':
            return {}

        # Decode HTML entities
        decoded_description = html.unescape(frontend_description)

        # Dictionary to store the hours
        opening_hours = {
            "Mon": "Closed",
            "Tue": "Closed",
            "Wed": "Closed",
            "Thu": "Closed",
            "Fri": "Closed",
            "Sat": "Closed",  # Default for Saturday
            "Sun": "Closed",  # Default for Sunday
        }

        # Map Spanish days to English
        days_map = {
            "Lunes": "Mon",
            "Martes": "Tue",
            "Miércoles": "Wed",
            "Jueves": "Thu",
            "Viernes": "Fri",
            "Sábado": "Sat",
            "Domingo": "Sun"
        }

        # Pattern 1: "Lunes a Viernes de 8:00 a.m. a 5:00 p.m."
        pattern_1 = r'Lunes\s*a\s*Viernes\s*de\s*(\d{1,2}:\d{2}\s*[a|p]\.m.)\s*a\s*(\d{1,2}:\d{2}\s*[a|p]\.m.)'

        # Pattern 2: "Lunes - Viernes 8:00 a.m. - 8:00 p.m."
        pattern_2 = r'Lunes\s*-\s*Viernes\s*(\d{1,2}:\d{2}\s*[a|p]\.m.\s*-\s*\d{1,2}:\d{2}\s*[a|p]\.m.)'

        # Pattern 3: "Lunes a Viernes: 8:00 a.m. - 5:00 p.m."
        pattern_3 = r'Lunes\s*a\s*Viernes\s*:\s*(\d{1,2}:\d{2}\s*[a|p]\.m.)\s*-\s*(\d{1,2}:\d{2}\s*[a|p]\.m.)'

        # Pattern 4: "Lunes a viernes de 8:00 a.m. a 5:00 p.m."
        pattern_4 = r'Lunes\s*a\s*viernes\s*de\s*(\d{1,2}:\d{2}\s*[a|p]\.m.)\s*a\s*(\d{1,2}:\d{2}\s*[a|p]\.m.)'

        # Pattern 5: "Lunes - Viernes: 8:00 a.m. - 8:00 p.m."
        pattern_5 = r'Lunes\s*-\s*Viernes\s*:\s*(\d{1,2}:\d{2}\s*[a|p]\.m.)\s*-\s*(\d{1,2}:\d{2}\s*[a|p]\.m.)'

        # Match Pattern 1: "Lunes a Viernes de"
        match_1 = re.search(pattern_1, decoded_description)

        # Match Pattern 2: "Lunes - Viernes"
        match_2 = re.search(pattern_2, decoded_description)

        # Match Pattern 3: "Lunes a Viernes:"
        match_3 = re.search(pattern_3, decoded_description)

        # Match Pattern 4: "Lunes a viernes de"
        match_4 = re.search(pattern_4, decoded_description)

        # Match Pattern 5: "Lunes - Viernes:"
        match_5 = re.search(pattern_5, decoded_description)

        # Handle Pattern 1: "Lunes a Viernes de"
        if match_1:
            start_time, end_time = match_1.groups()
            opening_hours["Mon"] = self.convert_to_24_hour_format(f"{start_time} - {end_time}")
            opening_hours["Tue"] = opening_hours["Mon"]
            opening_hours["Wed"] = opening_hours["Mon"]
            opening_hours["Thu"] = opening_hours["Mon"]
            opening_hours["Fri"] = opening_hours["Mon"]

        # Handle Pattern 2: "Lunes - Viernes"
        elif match_2:
            time_span = match_2.group(1)
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
                opening_hours[day] = self.convert_to_24_hour_format(time_span)

        # Handle Pattern 3: "Lunes a Viernes:"
        elif match_3:
            start_time, end_time = match_3.groups()
            opening_hours["Mon"] = self.convert_to_24_hour_format(f"{start_time} - {end_time}")
            opening_hours["Tue"] = opening_hours["Mon"]
            opening_hours["Wed"] = opening_hours["Mon"]
            opening_hours["Thu"] = opening_hours["Mon"]
            opening_hours["Fri"] = opening_hours["Mon"]

        # Handle Pattern 4: "Lunes a viernes de"
        elif match_4:
            start_time, end_time = match_4.groups()
            opening_hours["Mon"] = self.convert_to_24_hour_format(f"{start_time} - {end_time}")
            opening_hours["Tue"] = opening_hours["Mon"]
            opening_hours["Wed"] = opening_hours["Mon"]
            opening_hours["Thu"] = opening_hours["Mon"]
            opening_hours["Fri"] = opening_hours["Mon"]

        # Handle Pattern 5: "Lunes - Viernes:"
        elif match_5:
            start_time, end_time = match_5.groups()
            opening_hours["Mon"] = self.convert_to_24_hour_format(f"{start_time} - {end_time}")
            opening_hours["Tue"] = opening_hours["Mon"]
            opening_hours["Wed"] = opening_hours["Mon"]
            opening_hours["Thu"] = opening_hours["Mon"]
            opening_hours["Fri"] = opening_hours["Mon"]

        # Check for Saturday and Sunday if mentioned explicitly in the description
        if "Sábado" in decoded_description:
            saturday_match = re.search(r'Sábado\s*(\d{1,2}:\d{2}\s*[a|p]\.m.\s*-\s*\d{1,2}:\d{2}\s*[a|p]\.m.)', decoded_description)
            if saturday_match:
                opening_hours["Sat"] = self.convert_to_24_hour_format(saturday_match.group(1))

        if "Domingo" in decoded_description:
            sunday_match = re.search(r'Domingo\s*(\d{1,2}:\d{2}\s*[a|p]\.m.\s*-\s*\d{1,2}:\d{2}\s*[a|p]\.m.)', decoded_description)
            if sunday_match:
                opening_hours["Sun"] = self.convert_to_24_hour_format(sunday_match.group(1))

        return opening_hours

    def convert_to_24_hour_format(self, time_span):
        # Convert time from 12-hour format to 24-hour format
        time_span = time_span.lower().replace("a.m.", "am").replace("p.m.", "pm")

        pattern = r'(\d{1,2}):(\d{2})\s*(am|pm)\s*-\s*(\d{1,2}):(\d{2})\s*(am|pm)'
        match = re.match(pattern, time_span)

        if match:
            start_hour, start_minute, start_period, end_hour, end_minute, end_period = match.groups()

            # Convert start and end times to 24-hour format
            start_hour = int(start_hour)
            end_hour = int(end_hour)

            if start_period == "pm" and start_hour != 12:
                start_hour += 12
            elif start_period == "am" and start_hour == 12:
                start_hour = 0

            if end_period == "pm" and end_hour != 12:
                end_hour += 12
            elif end_period == "am" and end_hour == 12:
                end_hour = 0

            # Format the times as 24-hour time strings
            start_time = f"{start_hour:02}:{start_minute}"
            end_time = f"{end_hour:02}:{end_minute}"

            return f"{start_time}-{end_time}"

        return "Closed"
