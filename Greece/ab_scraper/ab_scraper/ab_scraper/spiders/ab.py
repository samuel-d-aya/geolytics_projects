from urllib.parse import urlencode
import datetime
import json
import scrapy


class AbSpider(scrapy.Spider):
    name = "ab"
    allowed_domains = ["www.ab.gr"]
    start_urls = ["https://www.ab.gr/api/v1/"]

    cookies = {
        "dtCookie": "v_4_srv_4_sn_3815F2B3130DF48F43E189417FDE70F2_perc_100000_ol_0_mul_1_app-3A440a591b5a5302d3_1",
        "PIM-SESSION-ID": "Ww05REzOYKFErkut",
        "rxVisitor": "1747404319761QEQ7F2IUASM62BDTPE3KDNUU3Q5PS893",
        "deviceSessionId": "b14d4074-762b-4857-988e-c8bce851c137",
        "grocery-ccatc": "CsZm0m8IbDDtpVNG99xT0DO8XgY",
        "dtSa": "-",
        "_abck": "43F56ADCF3FBEC2D44C3B797CA0B10ED~-1~YAAQIYR7XIt+DtCWAQAAVfBp2Q0HU41AH1y2D2RkuiXYGxJARsOTWwrmqMBH/U5FO/H77b9y+IlEngtJJLI5NnmXTrDWp0N8hoJW6VCkE1yOgzj128+y21ZeYDv5nc23Fafn9NgflYB+jgxyQqREbTXqX8+uZFN8uCkkNHWl2p4bve87iKR9SE+zzPblWWavOqMYADxkW2w8o53FoytTVjUeN8GW5vvsRld8SUtnMzI7UiqTDZ67oynH+gSW8uwmOnEpI5b9ymdzQNIpRxM5Nu24MqgqXmA+KDD6xKBKBXGdkQZNRiIw+IPvEdYrPXlBHeXW5TvSj1HU/3YZ4rDoS569yF7Xgv4Nd8yecSR59xLun4cWWmAmOzlU6fO3pT75xQcSYkbBiiWRt+qHoyV6ZHt/tC9MHyAfet8+n/3tQ9e4oYs4SuV5WzgA5tOSJF3lafthYnb9d15a8UjG8vcYz4Uhm4EKA1bQqTg=~-1~-1~-1",
        "groceryCookieLang": "gr",
        "liquidFeeThreshold": "0",
        "ak_bmsc": "34CA12D9C26A6DC70B7F2F4F1690A2BC~000000000000000000000000000000~YAAQIYR7XJGHDtCWAQAANv9p2RuJo5fHYztQPLcweMYKzuPWVYlMLPLHhV6d9vTCf3yptt23JX0mguCLTK6qCCw+G+qUxtcoz0OcR3swjO1gVAk07Y/d4N9/7YgLL32b4/ddIlZAv7OmjIjmf9ncouR9zPsiSryZt3iNcqmx+IDXI2ouhtIw/TUFQ2QZrrxagEz7J3cwZ3A+/zEmZf3vInR7UeCm4+ECvAZ+W8zmBhrVEmvfAyFbr/PwEwCnM3W15nwQ8FTgJdJ0AHK8N23k0hIzEJbMwBkdmDHKxybqGQsmyL67pHa+xyPJWh5Ips3BBqYjCyIPA+UX3nVgRcSSvC9Xl2Hu/gaUme1EzJBzbOZBXrynKtgVm0nhs+y99Wjs4XUkt1r2JS6I5wYjHQzm4KYuc1txBZ9ngs+YUFyELwzPhHgB74VgS2Ic1MjsmuteuQ==",
        "VersionedCookieConsent": "v%3A2%2Cessential%3A1%2Canalytics%3A0%2Csocial%3A0%2Cperso_cont%3A0%2Cperso_ads%3A0%2Cads_external%3A0",
        "AWSALB": "+veTVPl2vh1Wo/+FAoefL/qTb2/p3GUGyiMRFijGQQ+O7qMdDWLImBd07rpMpQbSGk1+BQVt1A3Wo6n+J6QICJ51pv8AkFasILG4ayxHC5u/A+VgV8vcPubwSFKq",
        "AWSALBCORS": "+veTVPl2vh1Wo/+FAoefL/qTb2/p3GUGyiMRFijGQQ+O7qMdDWLImBd07rpMpQbSGk1+BQVt1A3Wo6n+J6QICJ51pv8AkFasILG4ayxHC5u/A+VgV8vcPubwSFKq",
        "bm_sz": "8BA15684912CFEA21E733EBE974FEAF3~YAAQIYR7XNQZMtCWAQAAUMe72Rs45foO2yBh8mNN0aHcy8K8mH9zFFRX8NVf9QvWS9i/znBILOOHMP0mTkhJk3Q3Da5xIPkW9qMEnX1H8W0bam63N0j0I4nICrEF615g4J1pL3MDQ8bJX1oqFIkKWbPEQ+3qnmsrEeDoM4rnG3ghZ5ikBQAQgvba+5drm6x7S2BPa1lC/U52538RdSDSjdra3SS9sfryChazfjij/14jcl0tSEFDJ/Qqq+mwR0cAlw6qvmKDvslygQHsqvNMhhMHzwsMhvCwhZbhAliUN9/1L0QEeVpVz1TNRccKyNYuZFMwqqRHI/ai7XyJth1aPcSZtMaJnrBW3KQ72Ymjwi6U1UKSgLt9lFph6x8sdRoclC1htENBl8xv2/MAJIL+SZlRqzT1ssvwIAp0nhMMU0lsYb2L8e97lG4zYH0CnbNvCARP~3747889~3486260",
        "bm_sv": "4B19513D8435AD6B314A756DBE055E1F~YAAQIYR7XFAaMtCWAQAAsMi72RuPOZLbx4Fd2I/62F6R3TD9PWt/jP7i3rJp0qlZgC0Q7rjn5yLN0XY+Zmf3h9Cl++grPnmglOIVsN7jEDRAZ/Bszuyvn2MaeAamXepMDTSvkUGlJN8WjnP5uGAbOplDmfV+W0Sk3E2YEW6oc80Pw+6so/PFRrAWltSTNwCuE9KK7XqodajwidwGlHc4aadqxf2NHOrpw1gdhg9tJpM49c9pUTMWNJLdnzbhTg9X~1",
        "rxvt": "1747411488081|1747408258270",
        "dtPC": "4$209684092_514h-vEHRFCRJRDWAROSSGHQUTDHQUKNFRCKHM-0e0",
    }

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.7",
        "apollographql-client-name": "gr-ab-web-stores",
        "apollographql-client-version": "34022fea0f4ed59507c8e1fbc88bf897848cf8a4",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://www.ab.gr/storelocator",
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-apollo-operation-id": "c897678213f7d92d36808225b1cf003abdd0da61d6b57da7fd5f7d7c8aefd4a5",
        "x-apollo-operation-name": "GetStoreSearch",
        "x-default-gql-refresh-token-disabled": "true",
        # "cookie": "dtCookie=v_4_srv_4_sn_3815F2B3130DF48F43E189417FDE70F2_perc_100000_ol_0_mul_1_app-3A440a591b5a5302d3_1; PIM-SESSION-ID=Ww05REzOYKFErkut; rxVisitor=1747404319761QEQ7F2IUASM62BDTPE3KDNUU3Q5PS893; deviceSessionId=b14d4074-762b-4857-988e-c8bce851c137; grocery-ccatc=CsZm0m8IbDDtpVNG99xT0DO8XgY; dtSa=-; _abck=43F56ADCF3FBEC2D44C3B797CA0B10ED~-1~YAAQIYR7XIt+DtCWAQAAVfBp2Q0HU41AH1y2D2RkuiXYGxJARsOTWwrmqMBH/U5FO/H77b9y+IlEngtJJLI5NnmXTrDWp0N8hoJW6VCkE1yOgzj128+y21ZeYDv5nc23Fafn9NgflYB+jgxyQqREbTXqX8+uZFN8uCkkNHWl2p4bve87iKR9SE+zzPblWWavOqMYADxkW2w8o53FoytTVjUeN8GW5vvsRld8SUtnMzI7UiqTDZ67oynH+gSW8uwmOnEpI5b9ymdzQNIpRxM5Nu24MqgqXmA+KDD6xKBKBXGdkQZNRiIw+IPvEdYrPXlBHeXW5TvSj1HU/3YZ4rDoS569yF7Xgv4Nd8yecSR59xLun4cWWmAmOzlU6fO3pT75xQcSYkbBiiWRt+qHoyV6ZHt/tC9MHyAfet8+n/3tQ9e4oYs4SuV5WzgA5tOSJF3lafthYnb9d15a8UjG8vcYz4Uhm4EKA1bQqTg=~-1~-1~-1; groceryCookieLang=gr; liquidFeeThreshold=0; ak_bmsc=34CA12D9C26A6DC70B7F2F4F1690A2BC~000000000000000000000000000000~YAAQIYR7XJGHDtCWAQAANv9p2RuJo5fHYztQPLcweMYKzuPWVYlMLPLHhV6d9vTCf3yptt23JX0mguCLTK6qCCw+G+qUxtcoz0OcR3swjO1gVAk07Y/d4N9/7YgLL32b4/ddIlZAv7OmjIjmf9ncouR9zPsiSryZt3iNcqmx+IDXI2ouhtIw/TUFQ2QZrrxagEz7J3cwZ3A+/zEmZf3vInR7UeCm4+ECvAZ+W8zmBhrVEmvfAyFbr/PwEwCnM3W15nwQ8FTgJdJ0AHK8N23k0hIzEJbMwBkdmDHKxybqGQsmyL67pHa+xyPJWh5Ips3BBqYjCyIPA+UX3nVgRcSSvC9Xl2Hu/gaUme1EzJBzbOZBXrynKtgVm0nhs+y99Wjs4XUkt1r2JS6I5wYjHQzm4KYuc1txBZ9ngs+YUFyELwzPhHgB74VgS2Ic1MjsmuteuQ==; VersionedCookieConsent=v%3A2%2Cessential%3A1%2Canalytics%3A0%2Csocial%3A0%2Cperso_cont%3A0%2Cperso_ads%3A0%2Cads_external%3A0; AWSALB=+veTVPl2vh1Wo/+FAoefL/qTb2/p3GUGyiMRFijGQQ+O7qMdDWLImBd07rpMpQbSGk1+BQVt1A3Wo6n+J6QICJ51pv8AkFasILG4ayxHC5u/A+VgV8vcPubwSFKq; AWSALBCORS=+veTVPl2vh1Wo/+FAoefL/qTb2/p3GUGyiMRFijGQQ+O7qMdDWLImBd07rpMpQbSGk1+BQVt1A3Wo6n+J6QICJ51pv8AkFasILG4ayxHC5u/A+VgV8vcPubwSFKq; bm_sz=8BA15684912CFEA21E733EBE974FEAF3~YAAQIYR7XNQZMtCWAQAAUMe72Rs45foO2yBh8mNN0aHcy8K8mH9zFFRX8NVf9QvWS9i/znBILOOHMP0mTkhJk3Q3Da5xIPkW9qMEnX1H8W0bam63N0j0I4nICrEF615g4J1pL3MDQ8bJX1oqFIkKWbPEQ+3qnmsrEeDoM4rnG3ghZ5ikBQAQgvba+5drm6x7S2BPa1lC/U52538RdSDSjdra3SS9sfryChazfjij/14jcl0tSEFDJ/Qqq+mwR0cAlw6qvmKDvslygQHsqvNMhhMHzwsMhvCwhZbhAliUN9/1L0QEeVpVz1TNRccKyNYuZFMwqqRHI/ai7XyJth1aPcSZtMaJnrBW3KQ72Ymjwi6U1UKSgLt9lFph6x8sdRoclC1htENBl8xv2/MAJIL+SZlRqzT1ssvwIAp0nhMMU0lsYb2L8e97lG4zYH0CnbNvCARP~3747889~3486260; bm_sv=4B19513D8435AD6B314A756DBE055E1F~YAAQIYR7XFAaMtCWAQAAsMi72RuPOZLbx4Fd2I/62F6R3TD9PWt/jP7i3rJp0qlZgC0Q7rjn5yLN0XY+Zmf3h9Cl++grPnmglOIVsN7jEDRAZ/Bszuyvn2MaeAamXepMDTSvkUGlJN8WjnP5uGAbOplDmfV+W0Sk3E2YEW6oc80Pw+6so/PFRrAWltSTNwCuE9KK7XqodajwidwGlHc4aadqxf2NHOrpw1gdhg9tJpM49c9pUTMWNJLdnzbhTg9X~1; rxvt=1747411488081|1747408258270; dtPC=4$209684092_514h-vEHRFCRJRDWAROSSGHQUTDHQUKNFRCKHM-0e0",
    }

    params = {
        "operationName": "GetStoreSearch",
        "variables": '{"pageSize":9999,"lang":"gr","query":"","currentPage":0,"options":"STORELOCATOR_MINIFIED"}',
        "extensions": '{"persistedQuery":{"version":1,"sha256Hash":"9dc67fed7b358c14d80bbd04c6524ef76f4298a142ed7ab86732442271f4ad46"}}',
    }

    def start_requests(self):
        for url in self.start_urls:
            full_url = url + "?" + urlencode(self.params)
            yield scrapy.Request(
                url=full_url,
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse,  # type:ignore
            )

    def parse(self, response):  # type: ignore

        data = json.loads(response.text)  # type: ignore
        stores = data["data"]["storeSearchJSON"]["stores"]

        for store in stores:

            yield {
                "addr_full": store.get("address", {}).get("formattedAddress", {}),
                "brand": "AB",
                "city": store.get("address").get("town"),
                "country": "Greece",
                "extras": {
                    "brand": "AB",
                    "fascia": "AB",
                    "category": "Retail",
                    "edit_date": str(datetime.datetime.now().date()),
                    "lat_lon_source": "Third Party",
                },
                "lat": store.get("geoPoint", {}).get("latitude"),
                "lon": store.get("geoPoint", {}).get("longitude"),
                "name": f"AB {store.get("localizedName")}",
                "opening_hours": self.parse_opening_hours(store.get("nextOpeningDay")),  # type: ignore
                "phone": store.get("address", {}).get("phone"),
                "postcode": store.get("address", {}).get("postalCode"),
                "ref": store.get("id"),
                "state": None,
                "website": store.get("urlName"),
            }

    def parse_opening_hours(self, opening_hour):  # type: ignore
        greek_days = [
            "Δευτέρα",  # Monday
            "Τρίτη",  # Tuesday
            "Τετάρτη",  # Wednesday
            "Πέμπτη",  # Thursday
            "Παρασκευή",  # Friday
            "Σάββατο",  # Saturday
            "Κυριακή",  # Sunday
        ]

        result = {
            "Mon": "04:00-19:00",
            "Tue": "04:00-19:00",
            "Wed": "04:00-19:00",
            "Thu": "04:00-19:00",
            "Fri": "04:00-19:00",
            "Sat": "04:00-19:00",
            "Sun": "05:30-14:00",
        }
        if opening_hour.get("weekDay") in greek_days:  # type: ignore
            result = {  # type: ignore
                day: f"{opening_hour.get("openingTime").split()[-1][:-3]}-{opening_hour.get("closingTime").split()[-1][:-3]}" for day in result if opening_hour.get("weekDay") != "Κυριακή"  # type: ignore
            }
        return {"opening_hours": result}
