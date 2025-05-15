import re
import json
import datetime
from urllib.parse import urlencode
import scrapy


class ZaraSpider(scrapy.Spider):
    name = "zara"
    allowed_domains = ["www.zara.com"]
    start_urls = ["https://www.zara.com/gr/en/stores-locator/extended/search?"]

    lat_lon = [
        ["Athens (Αθήνα)", 37.98, 23.73],
        ["Lamia (Λαμία)", 38.9, 22.43],
        ["Thessaloniki (Θεσσαλονίκη)", 40.64, 22.93],
        ["Heraklion (Ηράκλειο)", 35.34, 25.13],
        ["Komotini (Κομοτηνή)", 41.12, 25.4],
        ["Ioannina (Ιωάννινα)", 39.66, 20.85],
        ["Corfu (Κέρκυρα)", 39.62, 19.92],
        ["Mytilene (Μυτιλήνη)", 39.1, 26.55],
        ["Tripoli (Τρίπολη)", 37.51, 22.37],
        ["Ermoupoli (Ερμούπολη)", 37.44, 24.94],
        ["Larissa (Λάρισα)", 39.64, 22.42],
        ["Patras (Πάτρα)", 38.25, 21.73],
        ["Kozani (Κοζάνη)", 40.3, 21.78],
        ["IOLKOU", 39.3804511, 22.9662135],
        ["", 40.846281, 25.877843],
        ["", 35.51327777, 24.015483330000002],
        ["", 38.466367, 23.596337],
        ["", 37.040487, 22.111723],
        ["", 36.449046, 28.221906],
        ["", 40.93748, 24.40943],
        ["", 39.665397, 20.849884],
        ["", 41.138122, 24.889473],
        ["", 41.15028, 24.148220000000002],
    ]

    cookies = {
        "MicrosoftApplicationsTelemetryDeviceId": "6118e168-58c3-45ec-ac0a-210b737fff73",
        "MicrosoftApplicationsTelemetryFirstLaunchTime": "2025-05-13T22:09:00.068Z",
        "MicrosoftApplicationsTelemetryDeviceId": "6118e168-58c3-45ec-ac0a-210b737fff73",
        "MicrosoftApplicationsTelemetryFirstLaunchTime": "2025-05-13T22:09:00.068Z",
        "access_token": "eyJ4NXQjUzI1NiI6ImV6eW96cXZrQjJqem1NMmZSNElBZklJWm5sYjZYN2VidUdwYmxhb2ZXeWciLCJraWQiOiIxNDExNTcwOTA5OTE2MDAyMzA0MiIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiIyMDAzMTk5NTA5NzY5IiwiYXVkaXRUcmFja2luZ0lkIjoiNzE1N2MxNGUtY2M5NC00MjU3LWE1YzQtZDI1NTM4ZTBjYmVlIiwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50LnphcmEuY29tIiwidG9rZW5OYW1lIjoiYWNjZXNzX3Rva2VuIiwic2Vzc2lvbklkIjoiNDgzOTcwMzYyNjk4MjMyMjE3NiIsInN0b3JlSWQiOiIxMTcwOCIsInVzZXJJZCI6IjIwMDMxOTk1MDk3NjkiLCJ1bmlxdWVVc2VySWQiOiIyMDAzMTk5NTA5NzY5IiwiYXVkIjoibWljLW1lY2FjY291bnRjb3JlLW9hdXRoMiIsImFjY291bnRJZCI6Ijk5ZmZhMWQzLTViN2YtNGQzOS1iODY5LTQ4N2Q5NWE5MDZhZCIsIm5iZiI6MTc0NzE3NDE3MywiaWRlbnRpdHlUeXBlIjoiRyIsImF1dGhfdGltZSI6MTc0NzE3NDE3MywicmVhbG0iOiIvemEvZ3Vlc3QvIiwidXNlclR5cGUiOiJjdXN0b21lciIsImV4cCI6MTc0NzI2MDU3MywidG9rZW5UeXBlIjoiSldUVG9rZW4iLCJhdXRoTWV0aG9kIjoiTGVnYWN5LlphcmEuU2Vzc2lvblRva2VuIiwiaWF0IjoxNzQ3MTc0MTczLCJhdXRoTGV2ZWwiOiIxIiwiYnJhbmQiOiJ6YSIsImp0aSI6Ijc2ZTNlNWE0LWIwNzQtNGI4Yy1hOTZiLWFiYzY1ODNkZmZkMyJ9.6hEN0jW5mFAY9ioJIEXysUMMKLXtd2crpwYShQNYvtJvSnLm0JCw7SklecIkm51RyKFyt57yg1ifrjJuFf5S_GYw40Zd4GXXmiX0pu_15P7KbWoce1STv2erm2197Kuop0ZlYmREGo8-N9DOY2Ulid1bnJp_S4VvfExY4-qOBZzENlldTkzwasA-578TO-lAs6cOJ9UIGX7PFiodg17HcFelIq8xtdIPvxARK7VQr2TmDgUft1c1srzMFcd0GmNEjvBA69DTkaD_y2_ODhT-nfmSxqDPSiLiUC3Ou9WCuX3xgxRoLKodaxiDtgKWLp6_XhAKzSMphsp8fTOWNtc685zEdCfTt47-OgImevL1Ls3a-_qn1xDi4m13ei62cHed_Xp81BK5ZJXgetEokdvIJ-M2wHVx3HPIksg6Wz88H2votJQhDojXqncF75r7bfyRcc7BX-iV_hgqJnyadAY4i9tkbRcd6eSUtWkill0xdJ1oXPI4tDx8QZ7Rurfomeyy6U3yrb4U4fvRtGZisOfaT1RQvgXRYUrABB6GzJb4n5Aug41SuCrn9c82lMaxlirgsnUvfoyvZdFFDzo5y-gE3rqSyAjxeLx_qTV54t5EeiSHOYMDRDxG-Omov7GtB8dN2SnKiWhL93WwUSEXThje71H3k2t70C-sxD9VJEe2dBY",
        "access_token_expires": "j%3A%222025-05-14T22%3A09%3A30.362Z%22",
        "user_type": "guest",
        "user_id": "2003199509769",
        "sids": "s%3A9PinH04Nmmdc2TLKNR9xYr4eC2L9yubz.436esX5U2UiOwgY42QbYtEgxT8863H1QOygjunuc8W4",
        "TS01ae8d30": "01aee7bf318d68832f4248fb941bbe78b20db5b2f83725ffca5a88327d01964df4dd5b7762cd248d5caab547f9b899c42f01d9d9fc",
        "ITXDEVICEID": "094d58c2f4826554042d9fe8df252282",
        "rid": "4ca04206-fc81-4583-8b0b-ad269ad8e18f",
        "UAITXID": "1c87fd0d9a856f4d3803969fe1a5156ca20fa67cb9746e66b8424665f611be80",
        "cart-was-updated-in-standard": "true",
        "OptanonAlertBoxClosed": "2025-05-13T22:09:08.834Z",
        "optimizelyEndUserId": "oeu1747174149361r0.23944603105549722",
        "optimizelySession": "0",
        "IDROSTA": "c7dd674485ac:2f9bc5813451104d55c357a24",
        "ITXSESSIONID": "c8c5d77e07d397730804ca965fa691b7",
        "ak_bmsc": "0ADFCA56AC4171AFC69AE2FAEABC0B54~000000000000000000000000000000~YAAQpnd7XMst8caWAQAAJgZmzRun/CqfU991GgTBj6k8lkB9L59LDLRRFFRWYzxRm1NYzEiHfPz8LrMAxCUF0q+5jY9e5SLQWMToBYpeZAT116gSgFISSDLM/0hER/vi0KVEB9Y2tTvQtr4u0l+9mD6gp13XWUDQhyRviA//3o6VvDlPMtiN6OpF2lNgw/68QkjHFbXOERqcbcFlGbhIn54Q9Bpr70jg2GozAZ5PXs4AvzN97nO0xti1sN45Zg9ShvNBYDh3Qdjz+c1rC8KMZ674U3odiFWPHYkQuh2BqLvTwqR9wErYSe2zfmDwkF1WZEmaUiwSw1YtoYVG+ayfz/8ai4gUlhr5CrKu115kRclI38cmQXxq5AoJifwtUNW4GTPc8VHaF+wu95DCTMjqStuGHJD6SpVPSFwOD8e9Z1+JaCXqlrpnYcOPJ5X/BsmkbjAh1rT8K2uRDhnU7mF0R2IdrdAdvXm2CTut1dmlzS70qUlKDnDZlyqBSP23InzfcGZBxsTWBSWdShinqr1e+szrRfA79X7ja7GskaGusAH1xJSnmQ==",
        "_abck": "4AD5EBCE68DD43EBC69ED06F062DC075~0~YAAQpnd7XKXb8caWAQAAbcZvzQ1hT6HE0AJfxACh72lTB0AOFdgBqKUOBGRp6UFHRpPXPeo6fCzBRE21D71KQJ4pVdcATYyRgfH8k7YEalq0g086jmiuIXVnA4rB1A7QKuWmlqhs5XNBVscPAhUt0Xor+5rJl3WmLU3IhHJftcFEbTqYmIk2ybu2RwIauu+DNuMxwP7fy9YAK7xwT5MKC+dE8VbxHkjgs6mG8j4pKhnIHFLt8zfdFY3KfQRQtgxO3XkG887riO6jvxk8pqj4b2XmWXAEHxOA2DPkSYLLP3hRAgd9v0fv5QpTf5PqZmjHbck2tsAgRZMQcC+a8CYD8HX2+i7O1TwXPNNGWp+/cz31EEHE5aPQf8uDTnTRGuH5GKMVNofyWGmRLksuiNvq3qrDCcgVZuEDPVLTGk1vYUnIMBKJO/X0EvAMsNPdV9DSoizIjUVaxYKnSHyG0SzLTlwZ3GVQ1m0r5leeTtcxSMZTzaA71pEW6N0lyWUgPmk+tjkwCf1n9xq+XurN00rkAFPkABP/vvJiWatSeQwuGZAHFO2GwUiZ0H6WE8P/JiWaW3PoykLGLA+GkSwxGl9vQE05eYhPkTWpzCqsqS63EWXkf8u5ittOd06lzB8ryEoUBIjF8SXl+Ls6F17hCzIyW0qnrTmm+uIvhc+dtFs2gB5AQzrnuMXQnZAJwqjMZ+grGTma2c7os/VNaalP+AM7ZvnD+E04lWpviSXa3h/CjG5kLvfDMeOYF5aG+28=~-1~-1~1747206188",
        "bm_sz": "20156CB8FBFD98D7AD886C0030DE560A~YAAQuHd7XJjhF8uWAQAAYDt2zRvdsL7Opqh5WFsRQ0mQoA2lt6TC6M8ZDUCZJadeq5lnrYawIUdaqDdvi4XUL1rBKVimr0NB5cG77xf4my9RMPirJmtLeohNHS5dl/VJ4+O1nXJbLkK0z2mDC0N/wREhvu3Qq9Q3Ib4SZaD+53TZHJHZNHGzFtnbPAfYFMiUhH/ykt3toPIobzTJpt1xLje8jaCFcJKoITH8RmKE1sxCMGq8dbX/XbThjeDxRKrr+jRTN4QzaIitgXkfRd1PesFeUrZdNJTi1Cfw+krU34/g7dzR1o/dpcZdtBxBjBuMWzd5HlnFXLZ/WARw0EAy0DeTk7VkkI3gzxtclFUTsK+esYX3R/l0cl4hwarFcmB6uXJUd9UB5/BDRh3TLVKjBNT8LW0ujSOHiHtnNlcV2lIlEkO3ZIfedfmudFUn4AMy1MmqzAzARqsCn58v0BCPZVl3EgIJ0Cr6PbacM+t4quaMs0b/XyOzJxMTtkRWpkYS71ZO44pORUMosDYML8qNEtMmifN5sYH+60pZxF9WtcMU7IKh~4539704~3749958",
        "TS0122c9b6": "01aee7bf318d68832f4248fb941bbe78b20db5b2f83725ffca5a88327d01964df4dd5b7762cd248d5caab547f9b899c42f01d9d9fc",
        "OptanonConsent": "isGpcEnabled=1&datestamp=Wed+May+14+2025+06%3A23%3A22+GMT%2B0000+(Greenwich+Mean+Time)&version=202503.2.0&browserGpcFlag=1&isIABGlobal=false&hosts=&consentId=2a666831-4b7b-4d06-8081-a03c11bd354a&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A0&intType=3&geolocation=GH%3BAA&AwaitingReconsent=false",
        "bm_sv": "7FC1578A52F8D03DCD2E6EF3DF0C26B6~YAAQuHd7XFoJGMuWAQAAna93zRsOOlS+hu/QCiJEik4GD2oErXw9Mmb8Sx4AyyGeY5xxZzwVMZdw47WeJhkwnwXAmWM7cJtv3/Dby3Aa5BxLQE+GYZQ1QcmiPyBXQV/SLk2ZjTvNEH8/fPTg+tlgu59K6fxnc45makRjK01bLu45bjvRKPdCMcoMXYOpL4N+DpmUOnBnzLSSJel0U1b52U8RUuGA2YR9UMIR26H28+x5W3JDKBCAVIuO1DiikMg=~1",
    }

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Bearer eyJ4NXQjUzI1NiI6ImV6eW96cXZrQjJqem1NMmZSNElBZklJWm5sYjZYN2VidUdwYmxhb2ZXeWciLCJraWQiOiIxNDExNTcwOTA5OTE2MDAyMzA0MiIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiIyMDAzMTk5NTA5NzY5IiwiYXVkaXRUcmFja2luZ0lkIjoiNzE1N2MxNGUtY2M5NC00MjU3LWE1YzQtZDI1NTM4ZTBjYmVlIiwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50LnphcmEuY29tIiwidG9rZW5OYW1lIjoiYWNjZXNzX3Rva2VuIiwic2Vzc2lvbklkIjoiNDgzOTcwMzYyNjk4MjMyMjE3NiIsInN0b3JlSWQiOiIxMTcwOCIsInVzZXJJZCI6IjIwMDMxOTk1MDk3NjkiLCJ1bmlxdWVVc2VySWQiOiIyMDAzMTk5NTA5NzY5IiwiYXVkIjoibWljLW1lY2FjY291bnRjb3JlLW9hdXRoMiIsImFjY291bnRJZCI6Ijk5ZmZhMWQzLTViN2YtNGQzOS1iODY5LTQ4N2Q5NWE5MDZhZCIsIm5iZiI6MTc0NzE3NDE3MywiaWRlbnRpdHlUeXBlIjoiRyIsImF1dGhfdGltZSI6MTc0NzE3NDE3MywicmVhbG0iOiIvemEvZ3Vlc3QvIiwidXNlclR5cGUiOiJjdXN0b21lciIsImV4cCI6MTc0NzI2MDU3MywidG9rZW5UeXBlIjoiSldUVG9rZW4iLCJhdXRoTWV0aG9kIjoiTGVnYWN5LlphcmEuU2Vzc2lvblRva2VuIiwiaWF0IjoxNzQ3MTc0MTczLCJhdXRoTGV2ZWwiOiIxIiwiYnJhbmQiOiJ6YSIsImp0aSI6Ijc2ZTNlNWE0LWIwNzQtNGI4Yy1hOTZiLWFiYzY1ODNkZmZkMyJ9.6hEN0jW5mFAY9ioJIEXysUMMKLXtd2crpwYShQNYvtJvSnLm0JCw7SklecIkm51RyKFyt57yg1ifrjJuFf5S_GYw40Zd4GXXmiX0pu_15P7KbWoce1STv2erm2197Kuop0ZlYmREGo8-N9DOY2Ulid1bnJp_S4VvfExY4-qOBZzENlldTkzwasA-578TO-lAs6cOJ9UIGX7PFiodg17HcFelIq8xtdIPvxARK7VQr2TmDgUft1c1srzMFcd0GmNEjvBA69DTkaD_y2_ODhT-nfmSxqDPSiLiUC3Ou9WCuX3xgxRoLKodaxiDtgKWLp6_XhAKzSMphsp8fTOWNtc685zEdCfTt47-OgImevL1Ls3a-_qn1xDi4m13ei62cHed_Xp81BK5ZJXgetEokdvIJ-M2wHVx3HPIksg6Wz88H2votJQhDojXqncF75r7bfyRcc7BX-iV_hgqJnyadAY4i9tkbRcd6eSUtWkill0xdJ1oXPI4tDx8QZ7Rurfomeyy6U3yrb4U4fvRtGZisOfaT1RQvgXRYUrABB6GzJb4n5Aug41SuCrn9c82lMaxlirgsnUvfoyvZdFFDzo5y-gE3rqSyAjxeLx_qTV54t5EeiSHOYMDRDxG-Omov7GtB8dN2SnKiWhL93WwUSEXThje71H3k2t70C-sxD9VJEe2dBY",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://www.zara.com/gr/en/z-stores-st1404.html",
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        # 'cookie': 'MicrosoftApplicationsTelemetryDeviceId=6118e168-58c3-45ec-ac0a-210b737fff73; MicrosoftApplicationsTelemetryFirstLaunchTime=2025-05-13T22:09:00.068Z; MicrosoftApplicationsTelemetryDeviceId=6118e168-58c3-45ec-ac0a-210b737fff73; MicrosoftApplicationsTelemetryFirstLaunchTime=2025-05-13T22:09:00.068Z; access_token=eyJ4NXQjUzI1NiI6ImV6eW96cXZrQjJqem1NMmZSNElBZklJWm5sYjZYN2VidUdwYmxhb2ZXeWciLCJraWQiOiIxNDExNTcwOTA5OTE2MDAyMzA0MiIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiIyMDAzMTk5NTA5NzY5IiwiYXVkaXRUcmFja2luZ0lkIjoiNzE1N2MxNGUtY2M5NC00MjU3LWE1YzQtZDI1NTM4ZTBjYmVlIiwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50LnphcmEuY29tIiwidG9rZW5OYW1lIjoiYWNjZXNzX3Rva2VuIiwic2Vzc2lvbklkIjoiNDgzOTcwMzYyNjk4MjMyMjE3NiIsInN0b3JlSWQiOiIxMTcwOCIsInVzZXJJZCI6IjIwMDMxOTk1MDk3NjkiLCJ1bmlxdWVVc2VySWQiOiIyMDAzMTk5NTA5NzY5IiwiYXVkIjoibWljLW1lY2FjY291bnRjb3JlLW9hdXRoMiIsImFjY291bnRJZCI6Ijk5ZmZhMWQzLTViN2YtNGQzOS1iODY5LTQ4N2Q5NWE5MDZhZCIsIm5iZiI6MTc0NzE3NDE3MywiaWRlbnRpdHlUeXBlIjoiRyIsImF1dGhfdGltZSI6MTc0NzE3NDE3MywicmVhbG0iOiIvemEvZ3Vlc3QvIiwidXNlclR5cGUiOiJjdXN0b21lciIsImV4cCI6MTc0NzI2MDU3MywidG9rZW5UeXBlIjoiSldUVG9rZW4iLCJhdXRoTWV0aG9kIjoiTGVnYWN5LlphcmEuU2Vzc2lvblRva2VuIiwiaWF0IjoxNzQ3MTc0MTczLCJhdXRoTGV2ZWwiOiIxIiwiYnJhbmQiOiJ6YSIsImp0aSI6Ijc2ZTNlNWE0LWIwNzQtNGI4Yy1hOTZiLWFiYzY1ODNkZmZkMyJ9.6hEN0jW5mFAY9ioJIEXysUMMKLXtd2crpwYShQNYvtJvSnLm0JCw7SklecIkm51RyKFyt57yg1ifrjJuFf5S_GYw40Zd4GXXmiX0pu_15P7KbWoce1STv2erm2197Kuop0ZlYmREGo8-N9DOY2Ulid1bnJp_S4VvfExY4-qOBZzENlldTkzwasA-578TO-lAs6cOJ9UIGX7PFiodg17HcFelIq8xtdIPvxARK7VQr2TmDgUft1c1srzMFcd0GmNEjvBA69DTkaD_y2_ODhT-nfmSxqDPSiLiUC3Ou9WCuX3xgxRoLKodaxiDtgKWLp6_XhAKzSMphsp8fTOWNtc685zEdCfTt47-OgImevL1Ls3a-_qn1xDi4m13ei62cHed_Xp81BK5ZJXgetEokdvIJ-M2wHVx3HPIksg6Wz88H2votJQhDojXqncF75r7bfyRcc7BX-iV_hgqJnyadAY4i9tkbRcd6eSUtWkill0xdJ1oXPI4tDx8QZ7Rurfomeyy6U3yrb4U4fvRtGZisOfaT1RQvgXRYUrABB6GzJb4n5Aug41SuCrn9c82lMaxlirgsnUvfoyvZdFFDzo5y-gE3rqSyAjxeLx_qTV54t5EeiSHOYMDRDxG-Omov7GtB8dN2SnKiWhL93WwUSEXThje71H3k2t70C-sxD9VJEe2dBY; access_token_expires=j%3A%222025-05-14T22%3A09%3A30.362Z%22; user_type=guest; user_id=2003199509769; sids=s%3A9PinH04Nmmdc2TLKNR9xYr4eC2L9yubz.436esX5U2UiOwgY42QbYtEgxT8863H1QOygjunuc8W4; TS01ae8d30=01aee7bf318d68832f4248fb941bbe78b20db5b2f83725ffca5a88327d01964df4dd5b7762cd248d5caab547f9b899c42f01d9d9fc; ITXDEVICEID=094d58c2f4826554042d9fe8df252282; rid=4ca04206-fc81-4583-8b0b-ad269ad8e18f; UAITXID=1c87fd0d9a856f4d3803969fe1a5156ca20fa67cb9746e66b8424665f611be80; cart-was-updated-in-standard=true; OptanonAlertBoxClosed=2025-05-13T22:09:08.834Z; optimizelyEndUserId=oeu1747174149361r0.23944603105549722; optimizelySession=0; IDROSTA=c7dd674485ac:2f9bc5813451104d55c357a24; ITXSESSIONID=c8c5d77e07d397730804ca965fa691b7; ak_bmsc=0ADFCA56AC4171AFC69AE2FAEABC0B54~000000000000000000000000000000~YAAQpnd7XMst8caWAQAAJgZmzRun/CqfU991GgTBj6k8lkB9L59LDLRRFFRWYzxRm1NYzEiHfPz8LrMAxCUF0q+5jY9e5SLQWMToBYpeZAT116gSgFISSDLM/0hER/vi0KVEB9Y2tTvQtr4u0l+9mD6gp13XWUDQhyRviA//3o6VvDlPMtiN6OpF2lNgw/68QkjHFbXOERqcbcFlGbhIn54Q9Bpr70jg2GozAZ5PXs4AvzN97nO0xti1sN45Zg9ShvNBYDh3Qdjz+c1rC8KMZ674U3odiFWPHYkQuh2BqLvTwqR9wErYSe2zfmDwkF1WZEmaUiwSw1YtoYVG+ayfz/8ai4gUlhr5CrKu115kRclI38cmQXxq5AoJifwtUNW4GTPc8VHaF+wu95DCTMjqStuGHJD6SpVPSFwOD8e9Z1+JaCXqlrpnYcOPJ5X/BsmkbjAh1rT8K2uRDhnU7mF0R2IdrdAdvXm2CTut1dmlzS70qUlKDnDZlyqBSP23InzfcGZBxsTWBSWdShinqr1e+szrRfA79X7ja7GskaGusAH1xJSnmQ==; _abck=4AD5EBCE68DD43EBC69ED06F062DC075~0~YAAQpnd7XKXb8caWAQAAbcZvzQ1hT6HE0AJfxACh72lTB0AOFdgBqKUOBGRp6UFHRpPXPeo6fCzBRE21D71KQJ4pVdcATYyRgfH8k7YEalq0g086jmiuIXVnA4rB1A7QKuWmlqhs5XNBVscPAhUt0Xor+5rJl3WmLU3IhHJftcFEbTqYmIk2ybu2RwIauu+DNuMxwP7fy9YAK7xwT5MKC+dE8VbxHkjgs6mG8j4pKhnIHFLt8zfdFY3KfQRQtgxO3XkG887riO6jvxk8pqj4b2XmWXAEHxOA2DPkSYLLP3hRAgd9v0fv5QpTf5PqZmjHbck2tsAgRZMQcC+a8CYD8HX2+i7O1TwXPNNGWp+/cz31EEHE5aPQf8uDTnTRGuH5GKMVNofyWGmRLksuiNvq3qrDCcgVZuEDPVLTGk1vYUnIMBKJO/X0EvAMsNPdV9DSoizIjUVaxYKnSHyG0SzLTlwZ3GVQ1m0r5leeTtcxSMZTzaA71pEW6N0lyWUgPmk+tjkwCf1n9xq+XurN00rkAFPkABP/vvJiWatSeQwuGZAHFO2GwUiZ0H6WE8P/JiWaW3PoykLGLA+GkSwxGl9vQE05eYhPkTWpzCqsqS63EWXkf8u5ittOd06lzB8ryEoUBIjF8SXl+Ls6F17hCzIyW0qnrTmm+uIvhc+dtFs2gB5AQzrnuMXQnZAJwqjMZ+grGTma2c7os/VNaalP+AM7ZvnD+E04lWpviSXa3h/CjG5kLvfDMeOYF5aG+28=~-1~-1~1747206188; bm_sz=20156CB8FBFD98D7AD886C0030DE560A~YAAQuHd7XJjhF8uWAQAAYDt2zRvdsL7Opqh5WFsRQ0mQoA2lt6TC6M8ZDUCZJadeq5lnrYawIUdaqDdvi4XUL1rBKVimr0NB5cG77xf4my9RMPirJmtLeohNHS5dl/VJ4+O1nXJbLkK0z2mDC0N/wREhvu3Qq9Q3Ib4SZaD+53TZHJHZNHGzFtnbPAfYFMiUhH/ykt3toPIobzTJpt1xLje8jaCFcJKoITH8RmKE1sxCMGq8dbX/XbThjeDxRKrr+jRTN4QzaIitgXkfRd1PesFeUrZdNJTi1Cfw+krU34/g7dzR1o/dpcZdtBxBjBuMWzd5HlnFXLZ/WARw0EAy0DeTk7VkkI3gzxtclFUTsK+esYX3R/l0cl4hwarFcmB6uXJUd9UB5/BDRh3TLVKjBNT8LW0ujSOHiHtnNlcV2lIlEkO3ZIfedfmudFUn4AMy1MmqzAzARqsCn58v0BCPZVl3EgIJ0Cr6PbacM+t4quaMs0b/XyOzJxMTtkRWpkYS71ZO44pORUMosDYML8qNEtMmifN5sYH+60pZxF9WtcMU7IKh~4539704~3749958; TS0122c9b6=01aee7bf318d68832f4248fb941bbe78b20db5b2f83725ffca5a88327d01964df4dd5b7762cd248d5caab547f9b899c42f01d9d9fc; OptanonConsent=isGpcEnabled=1&datestamp=Wed+May+14+2025+06%3A23%3A22+GMT%2B0000+(Greenwich+Mean+Time)&version=202503.2.0&browserGpcFlag=1&isIABGlobal=false&hosts=&consentId=2a666831-4b7b-4d06-8081-a03c11bd354a&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A0&intType=3&geolocation=GH%3BAA&AwaitingReconsent=false; bm_sv=7FC1578A52F8D03DCD2E6EF3DF0C26B6~YAAQuHd7XFoJGMuWAQAAna93zRsOOlS+hu/QCiJEik4GD2oErXw9Mmb8Sx4AyyGeY5xxZzwVMZdw47WeJhkwnwXAmWM7cJtv3/Dby3Aa5BxLQE+GYZQ1QcmiPyBXQV/SLk2ZjTvNEH8/fPTg+tlgu59K6fxnc45makRjK01bLu45bjvRKPdCMcoMXYOpL4N+DpmUOnBnzLSSJel0U1b52U8RUuGA2YR9UMIR26H28+x5W3JDKBCAVIuO1DiikMg=~1',
    }

    params = {
        "lat": "37.9838096",
        "lng": "23.7275388",
        "isDonationOnly": "false",
        "skipRestrictions": "true",
        "ajax": "true",
    }

    def start_requests(self):
        for capital in self.lat_lon:
            self.params["lat"] = capital[1]
            self.params["lng"] = capital[-1]
            full_url = self.start_urls[0] + urlencode(self.params)
            yield scrapy.Request(
                url=full_url,
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse,
            )

    def parse(self, response):

        data = json.loads(response.text)
        if data:

            for store in data:

                self.logger.info(f"\n\nZara {", ".join(store.get("addressLines"))}\n\n")
                self.logger.info(f"\n\nZara {store.get("openingHours")}\n\n")

                yield {
                    "addr_full": f"{", ".join(store.get("addressLines"))}, {store.get("zipCode")} {store.get("city")}",
                    "brand": store.get("kind"),
                    "city": store.get("city"),
                    "country": "Greece",
                    "extras": {
                        "brand": store.get("kind"),
                        "fascia": store.get("kind"),
                        "category": "Retail",
                        "edit_date": datetime.datetime.now().strftime("%Y%m%d"),
                        "lat_lon_source": "Google",
                    },
                    "lat": store.get("latitude"),
                    "lon": store.get("longitude"),
                    "name": f"Zara {", ".join(store.get("addressLines"))}",
                    "opening_hours": self.parse_opening_hours(
                        store.get("openingHours")
                    ),
                    "phone": store.get("phones")[0] if store.get("phones") else None,
                    "postcode": store.get("zipCode"),
                    "ref": store.get("id"),
                    "state": store.get("state"),
                    "website": store.get("url"),
                }

    def parse_opening_hours(self, opening_hour):

        days_mapping = {
            1: "Mon",
            2: "Tue",
            3: "Wed",
            4: "Thu",
            5: "Fri",
            6: "Sat",
            7: "Sun",
        }

        result = {}
        if opening_hour:
            for row in opening_hour:
                result[days_mapping.get(row.get("weekDay"))] = (
                    f"{row.get("openingHoursInterval")[0].get("openTime") if row.get("openingHoursInterval") else "Closed"}-{row.get("openingHoursInterval")[0].get("closeTime") if row.get("openingHoursInterval") else ""}"
                )
        else:
            for idx in range(1, 7):
                result[days_mapping.get(idx)] = "00:00-23:59"
        return {"opening_hours": result}
