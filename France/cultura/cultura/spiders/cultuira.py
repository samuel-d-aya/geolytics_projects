import scrapy
import json
import datetime

class CulturaSpider(scrapy.Spider):
    name = "cultura"
    start_urls = [
        'https://www.cultura.com/magento/graphql?query={stores(sort:{name:ASC}){total_count,total_pages,items{id,seller_code,user_ratings_total,rating,name,distance,inauguration_date,contact_phone,shop_type,url_key,images_gallery,position{latitude,longitude},opening_hours{dayofweek,start_time,end_time},special_opening_hours{date,end_time,start_time},special_closing_hours{date,end_time,start_time},address{street,address_additional,indication,postcode,city,country_code}}}}'
    ]

    def parse(self, response):
        data = json.loads(response.text)
        stores = data.get('data', {}).get('stores', {}).get('items', [])
        
        for store in stores:
            address = store.get('address', {})
            position = store.get('position', {})
            opening_hours = store.get('opening_hours', {})
            yield {
                'address': f"{address.get('postcode', '')}, {address.get('street', '')} {address.get('city', '')}",
                'city': address.get('city'),
                'country_code': address.get('country_code'),
                'brand': "Cultura",
                'extras': {
                    'brand': "Cultura",
                    'fascia': store.get('shop_type'),
                    'category': "Retail",
                    'edit_date': datetime.datetime.now().strftime('%Y%m%d'),
                    'lat_lon_source': "website",
                },
                'ref': store.get('id'),
                'name': store.get('name'),
                'phone': store.get('contact_phone'),
                'latitude': position.get('latitude'),
                'longitude': position.get('longitude'),
                'opening_hours': store.get('opening_hours'),
                'postcode': address.get('postcode'),
                'website': "https://www.cultura.com/les-magasins.html"    
            }