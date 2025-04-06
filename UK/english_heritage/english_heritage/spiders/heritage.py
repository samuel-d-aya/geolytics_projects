import scrapy
import json
import datetime

class HeritageSpider(scrapy.Spider):
    name = "heritage"
    start_urls = [
        "https://www.english-heritage.org.uk/api/PropertySearch/GetAll?page=1&place=&mp=false&fe=false"
    ]

    def parse(self, response):
        data = json.loads(response.text)
        results = data.get("Results", [])
        for result in results:
            path = result.get("Path")
            ref = result.get("ID")  # Extract the id as ref
            if path:
                full_url = f"https://www.english-heritage.org.uk{path}"
                yield scrapy.Request(full_url, callback=self.parse_details, cb_kwargs={"ref": ref})

    def parse_details(self, response, ref):
        script_data = response.css("#bodyTag > main > div > div > div.container.body-content > script:nth-child(1)::text").get()
        if script_data:
            json_data = json.loads(script_data)
            yield {
                "full_addr": f"{json_data.get('address', {}).get('streetAddress', '')}, "
                            f"{json_data.get('address', {}).get('addressLocality', '')}, "
                            f"{json_data.get('address', {}).get('addressRegion', '')} "
                            f"{json_data.get('address', {}).get('postalCode', '')}".strip(),
                "city": json_data.get("address", {}).get("addressLocality"),
                "country": "United Kingdom",
                "brand": "English Heritage",        
                "extras":{
                    "brand": "English Heritage",
                    "fascia": "English Heritage",
                    "category": "Heritage Site",
                    "edit_date": datetime.datetime.now().strftime( "%Y%m%d"),
                    "lat_lon_source": "website",
                },
                "lat": json_data.get("geo", {}).get("latitude"),
                "lon": json_data.get("geo", {}).get("longitude"),
                "opening_hours": {"opening_hours":{}},
                "phone": json_data.get("telephone"),
                "ref": ref, 
                "postcode": json_data.get("address", {}).get("postalCode"),
                "name": json_data.get("name"),
                "state": json_data.get("address", {}).get("addressRegion"),
                "website": response.url,
            }