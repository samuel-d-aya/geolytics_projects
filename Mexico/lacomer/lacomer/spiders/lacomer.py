import scrapy
import json
import datetime

class StoresSpider(scrapy.Spider):
    name = "lacomer"

    def start_requests(self):
        file_path = '/home/sam/geolytics_projects/Mexico/response_lacomer.json'
        yield scrapy.Request(url=f'file://{file_path}', callback=self.parse)

    def parse(self, response):
        data = json.loads(response.body)

        brands = {
            'listLacomer': 'La Comer',
            'listCity': 'City Market',
            'listFresko': 'Fresko',
            'listSumesa': 'Sumesa'
        }

        for list_name, brand in brands.items():
            stores = data.get(list_name, [])
            for store in stores:
                yield {
                    'addr_full': self.build_address(store),
                    'city': store.get('succLocal') or store.get('succMunic'),
                    'country': 'Mexico',
                    'brand': brand,
                    'extras': {
                        'brand': brand,
                        'fascia': brand,
                        'category': 'Retail',
                        'edit_date': datetime.datetime.now().strftime("%Y%m%d"),
                        'lat_lon_source': 'Website'
                    },
                    'lat': store.get('succLatitud'),
                    'lon': store.get('succLongitud'),
                    'opening_hours': {"opening_hours":self.build_opening_hours(store.get('horario'))},
                    'phone': store.get('succTel1'),
                    'ref': store.get('succId'),
                    'postcode': store.get('succCp'),
                    'name': store.get('succDes'),
                    'state': store.get('succEdo'),
                    'website': "https://www.lacomer.com.mx/lacomer/#!/conocenos/"
                }

    def build_address(self, store):
        parts = [
            store.get('succCalle', ''),
            store.get('succNumext', ''),
            store.get('succCol', ''),
            store.get('succMunic', ''),
            store.get('succEdo', '')
        ]
        return ', '.join([p for p in parts if p]).strip(', ')

    
    def build_opening_hours(self, horario):
        if not horario:
            return {}

        try:
            open_time, close_time = horario.split(' a ')
            open_time = self.format_time(open_time)
            close_time = self.format_time(close_time)
            return {
                day: f"{open_time}-{close_time}"
                for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            }
        except Exception as e:
            self.logger.error(f"Failed to parse horario '{horario}': {e}")
            return {}

    def format_time(self, time_str):
        if len(time_str) == 3:  # e.g., "730"
            time_str = '0' + time_str
        if len(time_str) == 4:  # e.g., "0730"
            return f"{time_str[:2]}:{time_str[2:]}"
        return time_str
