import datetime
import json
from typing import Iterator, Dict, Any, List, Union
from urllib.parse import urlencode
import scrapy
from scrapy.selector import Selector
from scrapy.http import Response, Request


class LidlHellasSpider(scrapy.Spider):
    name: str = "lidl_hellas"
    allowed_domains: List[str] = ["spatial.virtualearth.net"]
    start_urls: List[str] = [
        "https://spatial.virtualearth.net/REST/v1/data/c1070f3f97ad43c7845ab237eef704c0/Filialdaten-GR/Filialdaten-GR?"
    ]
    params: Dict[str, Any] = {
        "$select": "*,__Distance",
        "$filter": "Adresstyp eq 1",
        "key": "AjbddE6Qo-RdEfEZ74HKQxTGiCSM4dEoDL5uGGCiw7nOWaQiaKWSzPoGpezAfY_x",
        "$top": 250,
        "$skip": 0,
        "$format": "json",
    }

    def start_requests(self) -> Iterator[Request]:
        for url in self.start_urls:
            full_url: str = url + urlencode(self.params)
            yield scrapy.Request(url=full_url, callback=self.parse)

    def parse(self, response: Response) -> Iterator[Dict[str, Any]]:

        data: List[Dict[str, Any]] = json.loads(response.text)["d"]["results"]

        for store in data:

            yield {
                "addr_full": store.get("AddressLine"),
                "brand": "Lidl Hellas",
                "city": store.get("Locality") or store.get("CityDistrict"),
                "country": "Greece",
                "extras": {
                    "brand": "Lidl Hellas",
                    "fascia": "Lidl Hellas",
                    "category": "Retail",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.get("Latitude"),
                "lon": store.get("Longitude"),
                "name": f"Lidl {store.get("ShownStoreName")}",
                "opening_hours": self.parse_opening_hours(
                    store.get("OpeningTimes", "")
                ),
                "phone": store.get("phone"),
                "postcode": store.get("PostalCode"),
                "ref": store.get("EntityID"),
                "state": None,
                "website": f"https://www.lidl-hellas.gr/s/el-GR/anazitisi-katastimaton/{(store.get("Locality", "") or store.get("CityDistrict", "")).replace(" ", "-")}/{store.get("AddressLine", "").split(",")[0].replace(".", "").replace("%", "-").replace(" ", "-")}/",
            }

    def parse_opening_hours(self, opening_hours: str) -> Dict[str, Any]:

        opening_hours_list: List[str] = (
            Selector(text=opening_hours).css("body::text").getall()
        )
        days_maping: Dict[str, Any] = {
            "Δε": "Mon",
            "Τρ": "Tue",
            "Τε": "Wed",
            "Πέ": "Thu",
            "Πα": "Fri",
            "Σά": "Sat",
            "Κυ": "Sun",
        }

        result = {}

        for entry in opening_hours_list:
            if not entry.strip():
                continue
            parts = entry.strip().split()
            if len(parts) >= 2:
                day_abbr = parts[0]
                hours = parts[1]
                day = days_maping.get(day_abbr)
                if day:
                    result[day] = hours

        return {"opening_hours": result}
