import scrapy
import json
import datetime

class MasoutiSpider(scrapy.Spider):
    name = 'masouti'

    def start_requests(self):
        file_path = '/home/sam/geolytics_projects/Greece/masouti/response_masouti.json'
        with open(file_path, 'r', encoding='utf-8') as f:
            stores = json.load(f)

        for store in stores:
            # Instead of yielding a Request, just yield the parsed data directly
            yield {
                'addr_full': store.get('StoreDescrEn'),
                'city': store.get('CityEn'),
                'country': "Greece",
                'brand': "Masouti",
                'extra': {
                    'brand': "Masouti",
                    'fascia': store.get('KategoryIDEn'),
                    'category': "Retail",
                    'edit_date': datetime.datetime.now().strftime('%Y%m%d'),
                    'lat_lon_source': "Third Party",
                },
                'lat': store.get('Langitude'),
                'lon': store.get('Longitude'),
                'name': f"{"Masouti"} {store.get('CityEn')}",
                'opening_hours': {"opening_hours": {}},
                'Phone': store.get('Phone'),
                'postcode': store.get('ZipCode'),
                'ref': store.get('Storeid'),
                'state': store.get('CountryEn'),
                'website': "https://www.masoutis.gr/stores",
            }
