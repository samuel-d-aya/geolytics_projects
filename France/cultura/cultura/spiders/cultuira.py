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
                'addr_full': f"{address.get('postcode', '')}, {address.get('street', '')} {address.get('city', '')}",
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
                'lat': position.get('latitude'),
                'lon': position.get('longitude'),
                'opening_hours': self.convert_opening_hours(store.get('opening_hours')),
                'phone': store.get('contact_phone'),
                'ref': store.get('id'),
                'postcode': address.get('postcode'),
                'name': store.get('name'),
                'state': None,
                'website': "https://www.cultura.com/les-magasins.html"    
            }
    def convert_opening_hours(self,original_format):
        day_map = {
            "1": "Mon",
            "2": "Tue",
            "3": "Wed",
            "4": "Thu",
            "5": "Fri",
            "6": "Sat",
            "7": "Sun"
        }
        
        result = {
            "Mon": "Closed",
            "Tue": "Closed",
            "Wed": "Closed",
            "Thu": "Closed",
            "Fri": "Closed",
            "Sat": "Closed",
            "Sun": "Closed"
        }
        
        # Fill in the hours from the original format
        for day_info in original_format:
            day_name = day_map.get(day_info["dayofweek"])
            if day_name:
                start_time = day_info["start_time"]
                end_time = day_info["end_time"]
                result[day_name] = f"{start_time}-{end_time}"
        
        return {"opening_hours": result}