from typing import Iterable, Dict, Any, List
import json
import datetime
import scrapy
from scrapy.http.response import Response
from scrapy.http.request import Request


class KSupermarketSpider(scrapy.Spider):
    name = "k_supermarket"
    allowed_domains = ["www.k-ruoka.fi"]
    start_urls = ["https://www.k-ruoka.fi/kr-api/stores/search"]

    cookies = {
        "session": "b2fe2b6de693ecc948c5d36bb1bcf07e",
        "rxVisitor": "1747857939990U3IBDMGLHT0MDG06JDP5R1H79JSKULR2",
        "dtSa": "-",
        "dtCookie": "v_4_srv_1_sn_8E9E74AF4E82D4579BA205C251D6C1D3_perc_100000_ol_0_mul_1_app-3Aaf84350090df448d_1_rcs-3Acss_0",
        "win": "674x671",
        "__cf_bm": "YEGM54jRhBKp1QncpKuOAid6sPLdAP4G2Y2eGh8xNU4-1748666639-1.0.1.1-sNy8uCiUZhoYXRxS7hL_t7.6rWUkMFt2A4W0.74QclmQc6rdjye1NgaAUl8qTLRbH1NZoqOb27BZ8lICEhIbMMPGoeqK454NGSXlj00P_r0mTEnK.7xQEUWz9yabcfp.",
        "cf_clearance": "OZJUiKzHgMAl_Iy9_r_GGTkKfRKlYxQdMooTCI.LNFw-1748666650-1.2.1.1-yXzO_LzXzySvuxvWiKOvkwjyHjlIRm.EIwfypko30VUXBkBzbp1MDcVybKS8_77rp.1WJKe1pZxbMUn2U.SZT52s4VKWQiBwjiA3ZTfhWAGVR7nRjWumhxW3d4ZFaZmhp0mA.67cLUofikjkb8SC_CzDpcgJ3Yq.uDD1AtZLqy8YhQAIz8TT1khqgyeCDg1O.ism.v73akrIOrVktg4MxS8C88KNyqM_iQNS02DhKyv6K3Hw.PbWPfx.QCUEgygZxAUEDMRR7dYAGAq8snOg2GPux1SjATpl3zP2AeEwli.7gBY7yGJ2ibv64sejOmAW1XRMDrv0QB2rC1o.V6SdcRZEtNIJNuYYRFHJEommlwutUffJ2_McrwmeKClxc7za",
        "rxvt": "1748668555681|1748666562498",
        "dtPC": "1$261516567_795h17vDGWUPSADOVMKRGHCKKBDWPUBUEKHOECF-0e0",
    }

    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://www.k-ruoka.fi",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://www.k-ruoka.fi/k-supermarket?kaupat",
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-bitness": '"64"',
        "sec-ch-ua-full-version-list": '"Chromium";v="136.0.0.0", "Brave";v="136.0.0.0", "Not.A/Brand";v="99.0.0.0"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"19.0.0"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-dtpc": "1$261516567_795h17vDGWUPSADOVMKRGHCKKBDWPUBUEKHOECF-0e0",
        "x-k-build-number": "24387",
        "x-k-experiments": "ab4d.10001.1!d2ae.10003.0!a.00104.1!a.00111.0!a.00112.0!a.00114.1!a.00115.0",
        # 'cookie': 'session=b2fe2b6de693ecc948c5d36bb1bcf07e; rxVisitor=1747857939990U3IBDMGLHT0MDG06JDP5R1H79JSKULR2; dtSa=-; dtCookie=v_4_srv_1_sn_8E9E74AF4E82D4579BA205C251D6C1D3_perc_100000_ol_0_mul_1_app-3Aaf84350090df448d_1_rcs-3Acss_0; win=674x671; __cf_bm=YEGM54jRhBKp1QncpKuOAid6sPLdAP4G2Y2eGh8xNU4-1748666639-1.0.1.1-sNy8uCiUZhoYXRxS7hL_t7.6rWUkMFt2A4W0.74QclmQc6rdjye1NgaAUl8qTLRbH1NZoqOb27BZ8lICEhIbMMPGoeqK454NGSXlj00P_r0mTEnK.7xQEUWz9yabcfp.; cf_clearance=OZJUiKzHgMAl_Iy9_r_GGTkKfRKlYxQdMooTCI.LNFw-1748666650-1.2.1.1-yXzO_LzXzySvuxvWiKOvkwjyHjlIRm.EIwfypko30VUXBkBzbp1MDcVybKS8_77rp.1WJKe1pZxbMUn2U.SZT52s4VKWQiBwjiA3ZTfhWAGVR7nRjWumhxW3d4ZFaZmhp0mA.67cLUofikjkb8SC_CzDpcgJ3Yq.uDD1AtZLqy8YhQAIz8TT1khqgyeCDg1O.ism.v73akrIOrVktg4MxS8C88KNyqM_iQNS02DhKyv6K3Hw.PbWPfx.QCUEgygZxAUEDMRR7dYAGAq8snOg2GPux1SjATpl3zP2AeEwli.7gBY7yGJ2ibv64sejOmAW1XRMDrv0QB2rC1o.V6SdcRZEtNIJNuYYRFHJEommlwutUffJ2_McrwmeKClxc7za; rxvt=1748668555681|1748666562498; dtPC=1$261516567_795h17vDGWUPSADOVMKRGHCKKBDWPUBUEKHOECF-0e0',
    }

    json_data: Dict[str, Any] = {
        "query": "",
        "offset": 0,
        "limit": 100,
    }

    def start_requests(self) -> Iterable[Request]:
        for offset in range(0, 1058, 100):
            self.json_data["offset"] = offset
            yield scrapy.Request(
                method="POST",
                body=json.dumps(self.json_data),
                url=self.start_urls[0],
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse,
            )

    def parse(self, response: Response) -> Iterable[Dict[str, Any]]:
        stores = json.loads(response.text).get("results")

        for store in stores:

            yield {
                "addr_full": store.get("location"),
                "brand": store.get("chainName"),
                "city": store.get("location"),
                "country": "Finland",
                "extras": {
                    "brand": store.get("chainName"),
                    "fascia": store.get("chainName"),
                    "category": "Retail",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.get("geo").get("latitude"),
                "lon": store.get("geo").get("longitude"),
                "name": store.get("name"),
                "opening_hours": self.parse_opening_hours(store.get("openNextTwoDays")),
                "phone": None,
                "postcode": None,
                "ref": store.get("id"),
                "state": None,
                "website": f"https://www.k-ruoka.fi/kauppa/{store.get("slug")}",
            }

    def parse_opening_hours(
        self, opening_hours: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for open_hour in opening_hours:
            if (
                datetime.datetime.fromisoformat(
                    open_hour.get("date", "").replace("Z", "+00:00")
                ).weekday()
                < 5
            ):
                result.update(
                    [
                        ("Mon", f"{open_hour.get("opens")}-{open_hour.get("closes")}"),
                        ("Tue", f"{open_hour.get("opens")}-{open_hour.get("closes")}"),
                        ("Wed", f"{open_hour.get("opens")}-{open_hour.get("closes")}"),
                        ("Thu", f"{open_hour.get("opens")}-{open_hour.get("closes")}"),
                        ("Fri", f"{open_hour.get("opens")}-{open_hour.get("closes")}"),
                    ]
                )
            elif (
                datetime.datetime.fromisoformat(
                    open_hour.get("date", "").replace("Z", "+00:00")
                ).weekday()
                > 5
            ):
                result.update(
                    [
                        ("Sat", f"{open_hour.get("opens")}-{open_hour.get("closes")}"),
                        ("Sun", f"{open_hour.get("opens")}-{open_hour.get("closes")}"),
                    ]
                )
            else:
                result.update(
                    [
                        ("Mon", f"{"09:00"}-{open_hour.get("closes")}"),
                        ("Tue", f"{"09:00"}-{open_hour.get("closes")}"),
                        ("Wed", f"{"09:00"}-{open_hour.get("closes")}"),
                        ("Thu", f"{"09:00"}-{open_hour.get("closes")}"),
                        ("Fri", f"{"09:00"}-{open_hour.get("closes")}"),
                    ]
                )

        return {"opening_hours": result}
