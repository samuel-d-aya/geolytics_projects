from typing import Iterable, Dict, List, Union, Any
import datetime
import re
import json
import scrapy
from scrapy.http import Request, Response


class ShinsegaefoodSpider(scrapy.Spider):
    name = "shinsegaefood"
    allowed_domains = ["www.shinsegaefood.com"]
    start_urls = ["https://www.shinsegaefood.com/nobrandburger/store/store.sf"]

    cookies = {
        "JSESSIONID": "LajAU8ICK22GU6Gph3EXlgRvf0ipHHRgis6B2M9JytpPI8SNlBEsL3B9aGT82UX1.amV1c19kb21haW4vU1NHRm9vZDI=",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-GPC": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, headers=self.headers, cookies=self.cookies, callback=self.parse
            )

    def parse(self, response: Response) -> Iterable[Dict[str, Any]]:
        script_text = response.css("script:nth-child(13)::text").get() or ""
        data = self.parse_script_text(script_text)

        store_count = len(data)
        max_seq = max((int(store.get("seq", 0)) for store in data if store.get("seq")), default=0)
        self.logger.info(f"Total stores found: {store_count}")
        self.logger.info(f"Highest store seq: {max_seq}")

        for store in data:
            # Lat/Lon from imgUrl
            lat, lon = None, None
            img_url = store.get("imgUrl", "")
            if "," in img_url:
                parts = img_url.split(",")
                if len(parts) == 2:
                    lon, lat = parts[0].strip(), parts[1].strip()

            # Safe brandDesc parsing
            brand_desc = store.get("brandDesc", "")
            others = brand_desc.split("<br />")

            addr = self.extract_field(others, 0)
            phone = self.extract_field(others, 1)
            op_time_raw = self.extract_field(others, 2)
            op_time = op_time_raw.replace("~", "-") if op_time_raw else None

            yield {
                "addr_full": addr,
                "brand": "Shinesegaefood",
                "country": "Korea",
                "extras": {
                    "brand": "Shinesegaefood",
                    "fascia": "Shinesegaefood",
                    "category": "Rstaurant",
                    "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                    "lat_lon_source": "imgUrl",
                },
                "lat": lat,
                "lon": lon,
                "name": f"Shinesegaefood {store.get('title') or ''}",
                "opening_hours": self.parse_opening_hours(op_time),
                "phone": phone,
                "ref": store.get("seq") or None,
                "website": response.url,
            }

    def extract_field(self, parts: List[str], index: int) -> Union[str, None]:
        """Extracts and cleans value from parts[index] after colon, or returns None."""
        try:
            raw = parts[index]
            if ":" in raw:
                value = raw.split(":", 1)[-1]
                return self.clean_field(value)
        except IndexError:
            pass
        return None

    def clean_field(self, value: str) -> Union[str, None]:
        clean = re.sub(r"&[^;\s]+;", "", value)
        clean = re.sub(r"<[^>]+>", "", clean)
        clean = clean.strip()
        return clean if clean else None

    def parse_script_text(self, script_text: str) -> Union[List[Dict[str, Any]], Any]:
        pattern = r"var\s+storelist\s*=\s*(\[\s*{.*?}\s*\])"
        match = re.search(pattern, script_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse storelist JSON.")
        return []

    def parse_opening_hours(self, text: Union[str, None]) -> Dict[str, Any]:
        if not text:
            return {"opening_hours": {}}
        text = text.replace("오전", "AM").replace("오후", "PM")
        text = re.sub(r"&nbsp;|&amp;", " ", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        time_ranges = ""

        matches_24h = re.findall(r"(\d{1,2}:\d{2})\s*[-~]\s*(\d{1,2}:\d{2})", text)
        if matches_24h:
            time_ranges = f"{matches_24h[0][0]}-{matches_24h[0][1]}"

        matches_ampm = re.findall(r"(AM|PM)\s*(\d{1,2})시\s*[-~]\s*(AM|PM)\s*(\d{1,2})시", text)
        if matches_ampm:
            t1 = datetime.datetime.strptime(f"{matches_ampm[0][1]} {matches_ampm[0][0]}", "%I %p").strftime("%H:%M")
            t2 = datetime.datetime.strptime(f"{matches_ampm[0][3]} {matches_ampm[0][2]}", "%I %p").strftime("%H:%M")
            time_ranges = f"{t1}-{t2}"

        matches_ampm_simple = re.findall(r"(AM|PM)\s*(\d{1,2})\s*[-~]\s*(AM|PM)\s*(\d{1,2})", text)
        if matches_ampm_simple:
            t1 = datetime.datetime.strptime(f"{matches_ampm_simple[0][1]} {matches_ampm_simple[0][0]}", "%I %p").strftime("%H:%M")
            t2 = datetime.datetime.strptime(f"{matches_ampm_simple[0][3]} {matches_ampm_simple[0][2]}", "%I %p").strftime("%H:%M")
            time_ranges = f"{t1}-{t2}"

        result = {}
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            result[day] = time_ranges if time_ranges else None
        return {"opening_hours": result}
