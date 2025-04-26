import scrapy
import json
from datetime import datetime

class ChedrauiLocatorSpider(scrapy.Spider):
    name = "chedraui"
    allowed_domains = ["chedraui.com.mx"]
    start_urls = [
        "https://www.chedraui.com.mx/_v/public/graphql/v1?workspace=master&maxAge=short&appsEtag=remove&domain=store&locale=es-MX&operationName=getDocuments&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22a0afff5f19e837a70f3a7af8d60f121d36a3286670e5b90d134559436fb15a7f%22%2C%22sender%22%3A%22chedrauimx.locator%401.x%22%2C%22provider%22%3A%22vtex.store-graphql%402.x%22%7D%2C%22variables%22%3A%22eyJwYWdlU2l6ZSI6NTAwLCJhY3JvbnltIjoiQ1MiLCJmaWVsZHMiOlsiYWRkcmVzcyIsImlkX3N0b3JlIiwiYmFua19hdG1zIiwiYmF0aHJvb21fY3VzdG9tZXJzIiwiY2l0eSIsImNsb3NlX2hvdXIiLCJmdWxsX25hbWUiLCJob2xpZGF5X3NjaGVkdWxlcyIsImhvbWVfZGVsaXZlcnkiLCJsYXRpdHVkZSIsImxvbmdpdHVkZSIsIm5laWdoYm9yaG9vZCIsIm9wZW5faG91ciIsIm9wdGljYWxfc2VydmljZSIsInBhY2thZ2Vfc2VydmljZSIsInBhcmtpbmdfYmlrZXMiLCJwYXJraW5nX2NhcnMiLCJwYXJraW5nX2Zvcl9kaXNhYmxlZCIsInBhcmtpbmdfbW90b3MiLCJwYXJraW5nX3BpY2t1cCIsInBheW1lbnRfcmVtaXR0YW5jZXMiLCJwYXltZW50X3NlcnZpY2VzIiwicG9zdGFsX2NvZGUiLCJzZXJ2aWNlX2ZyZWlnaHQiLCJzaG9ydF9uYW1lIiwic3RhbXBlZF90aWNrZXQiLCJzdGF0ZSIsInN0b3JlX2Zvcm1hdCIsInN0b3JlX3BpY2t1cCJdfQ%3D%3D%22%7D"
    ]

    def parse(self, response):
        data = response.json()
        documents = data.get("data", {}).get("documents", [])

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for doc in documents:
            fields = {f['key']: f['value'] for f in doc.get("fields", [])}

            address = fields.get("address")
            city = fields.get("city", "").strip()
            lat = fields.get("latitude").replace(",", ".")
            lon = fields.get("longitude").replace(",", ".")
            store_id = fields.get("id_store")
            name = fields.get("full_name", "")
            postal_code = fields.get("postal_code") or fields.get("postalCode")

            open_raw = fields.get("open_hour")
            close_raw = fields.get("close_hour")

            opening_hours = {}
            if open_raw and close_raw:
                try:
                    open_24 = datetime.strptime(open_raw.strip(), "%I:%M %p").strftime("%H:%M")
                    close_24 = datetime.strptime(close_raw.strip(), "%I:%M %p").strftime("%H:%M")
                    opening_hours = {day: f"{open_24}-{close_24}" for day in days}
                except Exception as e:
                    self.logger.warning(f"Time parse error: {e}")
                    opening_hours = {}

            yield {
                "addr_full": address,
                "city": city,
                "country": "Mexico",
                "brand": "Chedraui",
                "extras": {
                    "brand": "Chedraui",
                    "fascia": "Chedraui",
                    "category": "Retail",
                    "edit_date": datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": 'google',
                },
                "lat": lat,
                "lon": lon,
                "opening_hours": {"opening_hours":opening_hours},
                "phone": None,
                "ref": store_id,
                "postcode": postal_code,
                "name": name,
                "state": None,
                "website": "https://www.chedraui.com.mx/encuentra-tu-tienda",
            }
