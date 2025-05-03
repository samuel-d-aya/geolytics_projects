import scrapy
import json
from datetime import datetime


class ChedrauiLocatorSpider(scrapy.Spider):
    name = "chedraui"
    allowed_domains = ["grupochedraui.com.mx"]

    def start_requests(self):
        for i in range(3, 40):  # from 3.json to 39.json
            url = f"https://www.grupochedraui.com.mx/wp-content/themes/chedraui/services/select_tiendas.php/{i}.json"
            yield scrapy.Request(url=url, callback=self.parse_store_list)

    def parse_store_list(self, response):
        try:
            stores = json.loads(response.text)
        except Exception as e:
            self.logger.warning(f"Failed to parse JSON at {response.url}: {e}")
            return

        for store in stores:
            name = (store.get("tienda") or "").strip()
            address = (store.get("direccion") or "").strip()
            lat_raw = store.get("latitud")
            lon_raw = store.get("longitud")
            lat = lat_raw.replace(",", ".") if lat_raw else None
            lon = lon_raw.replace(",", ".") if lon_raw else None
            phone = (store.get("telefono") or "").strip()

            yield {
                "name": name,
                "addr_full": address,
                "lat": lat,
                "lon": lon,
                "phone": phone,
                "country": "Mexico",
                "brand": "Chedraui",
                "extras": {
                    "brand": "Chedraui",
                    "fascia": "Chedraui",
                    "category": "Retail",
                    "edit_date": datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": 'website',
                },
                "ref": f"{name}_{lat}_{lon}",
                "website": "https://www.chedraui.com.mx/encuentra-tu-tienda",
            }
